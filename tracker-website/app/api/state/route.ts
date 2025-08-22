import { NextResponse } from 'next/server';
// Removed: import { cookies } from 'next/headers';

// Optional: Vercel KV for production persistence
let hasKV = !!process.env.KV_REST_API_URL && !!process.env.KV_REST_API_TOKEN;

// Lazy import to avoid errors when env not provided in dev
let kv: any = null;
if (hasKV) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    kv = require('@vercel/kv');
  } catch {
    hasKV = false;
  }
}

// In-memory fallback for local dev (non-persistent across restarts)
const memoryStore = new Map<string, { completion: Record<string, boolean>; updatedAt: number }>();

// Use a single global UID so your progress is identical across all devices
// Set TRACKER_GLOBAL_UID in your environment to customize the key; defaults to 'global'
const GLOBAL_UID = process.env.TRACKER_GLOBAL_UID || 'global';

const KEY = (uid: string) => `tracker:${uid}`;

async function getState(uid: string) {
  if (hasKV && kv?.kv) {
    const data = await kv.kv.get(KEY(uid));
    return (data as any) || null;
  }
  return memoryStore.get(uid) || null;
}

async function setState(uid: string, value: { completion: Record<string, boolean>; updatedAt: number }) {
  if (hasKV && kv?.kv) {
    await kv.kv.set(KEY(uid), value);
    return;
  }
  memoryStore.set(uid, value);
}

export async function GET() {
  const uid = GLOBAL_UID;
  const data = (await getState(uid)) || { completion: {}, updatedAt: Date.now() };
  return NextResponse.json(data);
}

export async function POST(req: Request) {
  const uid = GLOBAL_UID;

  let body: any = null;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const completion = (body?.completion || {}) as Record<string, boolean>;
  const updatedAt = typeof body?.updatedAt === 'number' ? body.updatedAt : Date.now();

  await setState(uid, { completion, updatedAt });

  return NextResponse.json({ ok: true, updatedAt });
}