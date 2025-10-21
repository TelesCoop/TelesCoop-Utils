"""
Script pour cloner un dossier Google Drive vers un autre emplacement
(même compte ayant accès aux deux drives)
Nécessite: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle

# Scopes nécessaires pour lire et écrire sur Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_drive(token_file='token.pickle', creds_file='credentials.json'):
    """Authentifie l'utilisateur et retourne le service Google Drive"""
    creds = None
    
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def get_folder_items(service, folder_id):
    """Récupère tous les fichiers et dossiers dans un dossier"""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()
    return results.get('files', [])

def create_folder(service, folder_name, parent_id=None):
    """Crée un nouveau dossier dans Google Drive"""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(
        body=file_metadata,
        fields='id, name'
    ).execute()
    
    print(f"✓ Dossier créé: {folder.get('name')}")
    return folder.get('id')

def copy_file_simple(service, file_id, file_name, dest_folder_id):
    """Copie un fichier en utilisant l'API copy de Google Drive"""
    file_metadata = {
        'name': file_name,
        'parents': [dest_folder_id]
    }
    
    try:
        copied_file = service.files().copy(
            fileId=file_id,
            body=file_metadata,
            fields='id, name'
        ).execute()
        
        print(f"  ✓ Fichier copié: {copied_file.get('name')}")
        return copied_file.get('id')
    except Exception as e:
        print(f"  ✗ Erreur lors de la copie de {file_name}: {str(e)}")
        return None

def clone_folder_recursive(service, source_folder_id, dest_parent_id=None, folder_name=None, level=0):
    """Clone récursivement un dossier et son contenu"""
    indent = "  " * level
    
    # Obtenir le nom du dossier source si non fourni
    if not folder_name:
        folder_metadata = service.files().get(
            fileId=source_folder_id,
            fields='name'
        ).execute()
        folder_name = folder_metadata.get('name')
    
    print(f"{indent}📁 Clonage du dossier: {folder_name}")
    
    # Créer le dossier de destination
    dest_folder_id = create_folder(service, folder_name, dest_parent_id)
    
    # Récupérer tous les éléments du dossier source
    items = get_folder_items(service, source_folder_id)
    
    if not items:
        print(f"{indent}  (dossier vide)")
        return dest_folder_id
    
    # Compter les éléments
    folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
    files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
    
    print(f"{indent}  Trouvé: {len(folders)} dossier(s), {len(files)} fichier(s)")
    
    # Copier les fichiers
    for i, item in enumerate(files, 1):
        print(f"{indent}  [{i}/{len(files)}]", end=" ")
        copy_file_simple(service, item['id'], item['name'], dest_folder_id)
    
    # Traiter les sous-dossiers récursivement
    for item in folders:
        clone_folder_recursive(service, item['id'], dest_folder_id, item['name'], level + 1)
    
    return dest_folder_id

def list_shared_drives(service):
    """Liste tous les drives partagés accessibles"""
    try:
        results = service.drives().list(pageSize=100).execute()
        drives = results.get('drives', [])
        
        if drives:
            print("\n📂 Drives partagés disponibles:")
            for i, drive in enumerate(drives, 1):
                print(f"  {i}. {drive['name']} (ID: {drive['id']})")
        else:
            print("\nAucun drive partagé trouvé.")
        
        return drives
    except Exception as e:
        print(f"Erreur lors de la récupération des drives partagés: {str(e)}")
        return []

def main():
    print("=" * 60)
    print("    SCRIPT DE CLONAGE GOOGLE DRIVE")
    print("=" * 60)
    print()
    
    # Authentification
    print("🔐 Authentification en cours...")
    service = authenticate_drive()
    print("✓ Authentification réussie!\n")
    
    # Afficher les drives partagés disponibles (optionnel)
    list_drives = input("Voulez-vous voir la liste des drives partagés ? (o/n): ").lower()
    if list_drives == 'o':
        list_shared_drives(service)
        print()
    
    # ID du dossier source
    print("📍 DOSSIER SOURCE")
    print("   (Trouvez l'ID dans l'URL: drive.google.com/drive/folders/[ID])")
    source_folder_id = input("   Entrez l'ID du dossier à cloner: ").strip()
    
    # ID du dossier de destination (optionnel)
    print("\n📍 DOSSIER DESTINATION")
    print("   (Laissez vide pour cloner à la racine de 'Mon Drive')")
    dest_parent_id = input("   Entrez l'ID du dossier parent destination: ").strip()
    dest_parent_id = dest_parent_id if dest_parent_id else None
    
    print("\n" + "=" * 60)
    print("🚀 DÉMARRAGE DU CLONAGE")
    print("=" * 60)
    print()
    
    try:
        clone_folder_recursive(service, source_folder_id, dest_parent_id)
        
        print("\n" + "=" * 60)
        print("✅ CLONAGE TERMINÉ AVEC SUCCÈS!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")

if __name__ == '__main__':
    main()