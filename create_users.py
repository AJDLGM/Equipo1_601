from auth.auth import register_user

print("Creando usuarios de prueba...")

register_user("externo", "123", "externo")
register_user("operativo", "123", "operativo")
register_user("coordinador", "123", "coordinador")
register_user("administrador", "123", "admin")

print("Usuarios creados correctamente")
