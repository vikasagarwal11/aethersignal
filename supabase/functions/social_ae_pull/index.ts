// Supabase Edge Function for daily Social AE pulls
// Deploy: supabase functions deploy social_ae_pull

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Get Supabase client with service role key
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get API endpoint from environment (your FastAPI/Render endpoint)
    const apiEndpoint = Deno.env.get("SOCIAL_AE_API_ENDPOINT") || 
      "https://your-api-endpoint.onrender.com/social/daily";

    console.log(`Calling API endpoint: ${apiEndpoint}`);

    // Call your Python API endpoint
    const response = await fetch(apiEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${Deno.env.get("API_SECRET_KEY") || ""}`,
      },
      body: JSON.stringify({
        source: "supabase_cron",
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("API response:", data);

    // Log pull history
    const { error: logError } = await supabase
      .from("pull_history")
      .insert({
        pull_date: new Date().toISOString(),
        drug_terms: "default_watchlist",
        platforms: "reddit",
        posts_fetched: data.inserted || data.posts_fetched || 0,
        posts_new: data.inserted || data.posts_stored || 0,
        posts_duplicate: data.duplicates || 0,
        status: data.success ? "success" : "error",
        error_message: data.error || null,
      });

    if (logError) {
      console.error("Error logging pull history:", logError);
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: "Daily pull triggered",
        api_response: data,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error) {
    console.error("Error in social_ae_pull function:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});

