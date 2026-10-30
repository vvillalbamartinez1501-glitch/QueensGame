import os
import json

def consolidar_mapas(carpeta_origen="mapas", archivo_destino="mapas.json"):
    mapas_totales = {}

    # Verificar si la carpeta existe
    if not os.path.exists(carpeta_origen):
        print(f"❌ Error: No se encontró la carpeta '{carpeta_origen}'.")
        print(f"Asegúrate de haber creado la carpeta '{carpeta_origen}' y colocado dentro los archivos .json.")
        return

    # Buscar todos los archivos .json en la carpeta
    archivos_json = [f for f in os.listdir(carpeta_origen) if f.endswith('.json')]

    if not archivos_json:
        print(f"⚠️ No se encontraron archivos .json dentro de la carpeta '{carpeta_origen}'.")
        return

    print(f"📁 Encontrados {len(archivos_json)} archivos en '{carpeta_origen}'. Procesando...")

    # Leer y combinar cada JSON
    for archivo in archivos_json:
        ruta_completa = os.path.join(carpeta_origen, archivo)
        try:
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                data = json.load(f)

                for clave, lista_mapas in data.items():
                    if clave not in mapas_totales:
                        mapas_totales[clave] = []
                    # Extiende la lista para no sobrescribir si hay mapas repetidos en clave
                    mapas_totales[clave].extend(lista_mapas)

            print(f"  [✓] Procesado: {archivo}")
        except Exception as e:
            print(f"  [X] Error al leer {archivo}: {e}")

    # Ordenar las claves numéricamente ("4", "5", "6", etc.)
    mapas_ordenados = {
        k: mapas_totales[k]
        for k in sorted(mapas_totales.keys(), key=lambda x: int(x) if x.isdigit() else x)
    }

    # Guardar en mapas.json con formato compacto sin espacios innecesarios
    with open(archivo_destino, 'w', encoding='utf-8') as f:
        json.dump(mapas_ordenados, f, ensure_ascii=False, separators=(',', ':'))

    print("\n==========================================")
    print("¡FUSIÓN COMPLETADA CON ÉXITO!")
    print("Resumen de mapas contenidos en mapas.json:")
    for clave, lista in mapas_ordenados.items():
        print(f" - Tamaño {clave}x{clave}: {len(lista)} mapas")
    print(f"\nArchivo final guardado en: {archivo_destino}")

if __name__ == "__main__":
    consolidar_mapas()