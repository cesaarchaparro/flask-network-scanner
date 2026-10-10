from flask import Flask, render_template, request
import platform
import subprocess
import concurrent.futures
import ipaddress
import socket

app = Flask(__name__)

def check_tcp_port(ip, port, timeout=0.8):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            return result == 0
    except Exception:
        return False

def check_ip(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
    timeout_val = "1000" if platform.system().lower() == "windows" else "1"
    
    cmd = ["ping", param, "1", timeout_param, timeout_val, str(ip)]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if result.returncode == 0:
        return (str(ip), "Ocupada", "Responde Ping")
    
    puertos_comunes = [80, 443, 22]
    for puerto in puertos_comunes:
        if check_tcp_port(ip, puerto):
            return (str(ip), "Ocupada", f"Ping bloqueado (Puerto {puerto} activo)")
            
    return (str(ip), "Libre", "Sin respuesta")

def es_ip_privada(ip_str):
    return ipaddress.ip_address(ip_str).is_private

@app.route("/", methods=["GET", "POST"])
def index():
    publicas_libres, publicas_ocupadas = [], []
    privadas_libres, privadas_ocupadas = [], []
    escaneado = False

    if request.method == "POST":
        texto_ips = request.form.get("ips_input", "")
        # Limpiar y separar las IPs por líneas o comas
        ips_to_scan = [ip.strip() for ip in texto_ips.replace(",", "\n").splitlines() if ip.strip()]
        
        if ips_to_scan:
            escaneado = True
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                results = executor.map(check_ip, ips_to_scan)
                
            for ip, status, detalle in results:
                item = {"ip": ip, "detalle": detalle}
                if es_ip_privada(ip):
                    if status == "Libre":
                        privadas_libres.append(item)
                    else:
                        privadas_ocupadas.append(item)
                else:
                    if status == "Libre":
                        publicas_libres.append(item)
                    else:
                        publicas_ocupadas.append(item)

    return render_template("index.html", 
                           escaneado=escaneado,
                           publicas_libres=publicas_libres,
                           publicas_ocupadas=publicas_ocupadas,
                           privadas_libres=privadas_libres,
                           privadas_ocupadas=privadas_ocupadas)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)