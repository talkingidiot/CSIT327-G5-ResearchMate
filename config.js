import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'

const SUPABASE_URL = 'https://rewbugqelirdszylnayk.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJld2J1Z3FlbGlyZHN6eWxuYXlrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDc1MDMsImV4cCI6MjA3NDcyMzUwM30.tLt6T_KNhpcjPLD2FwQzTd_aFbJeB_6Tj2g981zRdIM'

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
