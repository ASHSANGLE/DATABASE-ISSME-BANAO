// ============================================================
//  GoldenSage – Supabase Configuration
//  ⚠️ Replace the values below with your actual project keys
//  Get them from: Supabase Dashboard → Project Settings → API
// ============================================================

const SUPABASE_URL  = 'https://bymptkovosihlyvfqruw.supabase.co';   // 🔁 Replace this
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ5bXB0a292b3NpaGx5dmZxcnV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NDM5MTEsImV4cCI6MjA4NzUxOTkxMX0.TiioddoZkAhNurT11yU5BgOYztNIN2kSrKU0c-p4yD4';          // 🔁 Replace this

// Use the CDN's createClient correctly
const { createClient } = supabase;
const supabaseClient   = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);