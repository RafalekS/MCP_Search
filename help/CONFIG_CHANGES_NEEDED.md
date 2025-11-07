# Configuration Changes for Parser Fixes

## Sources to Remove (Broken/Paid)

Remove these sections from your `config/conf.ini`:

```ini
# REMOVE - Now requires payment
[SOURCE_aiagentstore.ai]
# ... entire section

# REMOVE - Now requires payment
[SOURCE_prompthero.com]
# ... entire section
```

Also update the CATEGORIES section to remove references:

```ini
[CATEGORIES]
# OLD:
# ai_agents = aiagentstore.ai,aiagentsdirectory.com,agent.ai,...
# ai_prompts = promptbase.com,prompthero.com,promptrr.io,...

# NEW:
ai_agents = aiagentsdirectory.com,agent.ai,microsoft_agent_store,google_cloud_ai_agent_marketplace,aws_ai_agent_marketplace
ai_prompts = promptbase.com,promptrr.io,prompti.ai,flowgpt.com,chatx.ai,aiprm.com
```

## Sources to Fix

### dxt.so/dxts - Wrong Query Parameter

**OLD:**
```ini
[SOURCE_dxt.so/dxts]
search_endpoint = https://dxt.so/dxts?q={query}
```

**NEW:**
```ini
[SOURCE_dxt.so/dxts]
search_endpoint = https://dxt.so/dxts?query={query}
```

## Parser Fixes Applied

1. ✅ Added comprehensive navigation filter list (Latest, Official, Featured, View all, etc.)
2. ✅ Added empty result detection ("No servers found", "No results found", etc.)
3. ✅ Improved result validation to skip generic names

## Next Steps

After making these config changes:
1. Restart the application
2. Test with search term "n8n"
3. Verify:
   - claudemcp.com returns 0 results (correct - site shows "No servers found")
   - dxt.services shows actual tools, not navigation
   - dxt.so/dxts shows 60 results instead of 3

## How to Edit Config

**Windows:**
```powershell
notepad config\conf.ini
```

**Linux/Mac:**
```bash
nano config/conf.ini
```

Search for the SOURCE_ sections mentioned above and make the changes.
