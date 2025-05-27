import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USR_CMDS_DIR = os.path.join(BASE_DIR, "CommandRoles")

if not os.path.isdir(USR_CMDS_DIR):
    os.makedirs(USR_CMDS_DIR)

USR_AUTH_FILE = os.path.join(USR_CMDS_DIR, "usr_auth_roles.txt")

def load_usr_roles():
    data = {}
    if os.path.exists(USR_AUTH_FILE):
        with open(USR_AUTH_FILE, "r") as file:
            for line in file:
                if not line:
                    continue
                line = line.strip()
                try:
                    guild_str, role_str = line.split(":", 1)
                    guild_id = int(guild_str.strip())
                    roles =  [int(role.strip()) for role in role_str.split(",") if role.strip()]
                    data[guild_id] = roles
                except Exception as e:
                    print(f"Error loading roles authorized to make user commands: {line} : {e}")
                    
                return data
            
def save_usr_auth_roles(data) -> None:
    with open(USR_AUTH_FILE, "w", encoding="utf-8") as file:
        for guild_id, roles, in data.items():
            line = f"{guild_id}: {', '.join(map(str, roles))}"
            file.write(line)                