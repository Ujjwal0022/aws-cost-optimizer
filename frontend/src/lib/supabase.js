import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "https://szguxkshtxsqiczrytgf.supabase.co";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "sb_publishable_4tWQMKjivhz27Wvz9V24MQ_C_R8I4DG";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
