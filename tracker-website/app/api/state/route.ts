import { NextResponse } from 'next/server';

// Ensure Vercel KV is only imported when environment variables are set
let kv: any;
if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
  try {
    kv = require('@vercel/kv').kv;
  } catch (error) {
    console.error('Failed to load @vercel/kv:', error);
    kv = null;
  }
}

// In-memory fallback for local dev or if KV fails to initialize
const memoryStore = new Map<string, any>();

// Use a single global UID so progress is identical across all devices
const GLOBAL_UID = process.env.TRACKER_GLOBAL_UID || 'global-tracker-state';
const KEY = `tracker:${GLOBAL_UID}`;

async function getState() {
  if (kv) {
    try {
      const data = await kv.get(KEY);
      console.log(`[API GET] Fetched from KV for key "${KEY}". Data exists: ${!!data}`);
      return data || null;
    } catch (error) {
      console.error('[API GET] Error fetching from KV:', error);
      return null; // Return null on error
    }
  }
  // Fallback for local development
  const memoryData = memoryStore.get(KEY);
  console.log(`[API GET] Fetched from memoryStore. Data exists: ${!!memoryData}`);
  return memoryData || null;
}

async function setState(value: any) {
  if (kv) {
    try {
      await kv.set(KEY, value);
      console.log(`[API SET] Successfully set data in KV for key "${KEY}".`);
    } catch (error) {
      console.error('[API SET] Error setting data in KV:', error);
    }
    return;
  }
  // Fallback for local development
  memoryStore.set(KEY, value);
  console.log(`[API SET] Set data in memoryStore.`);
}

export async function GET() {
  console.log('[API GET] Received GET request.');
  const data = await getState();
  // Always return a valid structure
  return NextResponse.json(data || { completion: {}, updatedAt: Date.now() });
}

export async function POST(req: Request) {
  console.log('[API POST] Received POST request.');
  let body: any;
  try {
    body = await req.json();
  } catch {
    console.error('[API POST] Invalid JSON in request body.');
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const incomingCompletion = (body?.completion || {}) as Record<string, boolean>;
  console.log(`[API POST] Received ${Object.keys(incomingCompletion).length} completion keys from client.`);

  // --- MERGE LOGIC ---
  const currentState = await getState();
  const currentCompletion = currentState?.completion || {};
  console.log(`[API POST] Current state in DB has ${Object.keys(currentCompletion).length} keys.`);

  const newCompletion = {
    ...currentCompletion,
    ...incomingCompletion,
  };
  console.log(`[API POST] Merged state now has ${Object.keys(newCompletion).length} keys.`);

  const updatedAt = Date.now();
  await setState({ completion: newCompletion, updatedAt });

  return NextResponse.json({ ok: true, updatedAt });
}

// This forces the API route to be dynamic and not cached
export const dynamic = 'force-dynamic';
