import os
from dotenv import load_dotenv

print("--- DIAGNOSTIC DÉMARRÉ ---")

# 1. Où sommes-nous ?
cwd = os.getcwd()
print(f"📍 Dossier actuel (CWD) : {cwd}")

# 2. Qu'y a-t-il ici ? (C'est là qu'on verra si c'est .env ou .env.txt)
files = os.listdir(cwd)
print("📂 Fichiers détectés :")
for f in files:
    if ".env" in f:
        print(f"   -> {f}")

# 3. Tentative de chargement
load_dotenv()
google_key = os.getenv("GOOGLE_API_KEY")
tmdb_key = os.getenv("TMDB_API_KEY")

print("\n🔑 Vérification des clés :")
if google_key:
    print(f"   - GOOGLE_API_KEY : Trouvée (Commence par {google_key[:5]}...)")
else:
    print("   - GOOGLE_API_KEY : ❌ NON TROUVÉE")

if tmdb_key:
    print(f"   - TMDB_API_KEY   : Trouvée")
else:
    print("   - TMDB_API_KEY   : ❌ NON TROUVÉE")

print("--------------------------")