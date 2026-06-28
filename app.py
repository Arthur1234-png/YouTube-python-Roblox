import os
import cv2
import flask
from flask import jsonify, request
from pytubefix import YouTube

app = flask.Flask(__name__)

# Configurações da Tela (Mantenha exatamente igual ao script do Roblox)
LARGURA = 32
ALTURA = 24

# Variáveis globais para gerenciar o estado do vídeo
video_captura = None
video_carregado = False
titulo_atual = "Nenhum vídeo carregado"

@app.route('/carregar-video', methods=['POST'])
def carregar_video():
    global video_captura, video_carregado, titulo_atual
    dados = request.json or {}
    url = dados.get("url")
    
    if not url:
        return jsonify({"status": "erro", "mensagem": "A URL fornecida está vazia"}), 400
        
    try:
        print(f"Buscando informações e baixando a URL: {url}")
        yt = YouTube(url)
        titulo_atual = yt.title
        
        # Filtra para baixar na menor resolução (144p) em formato MP4
        stream = yt.streams.filter(res="144p", file_extension="mp4").first()
        if not stream:
            stream = yt.streams.filter(file_extension="mp4").first()
            
        # Remove o arquivo de vídeo anterior se ele existir
        if os.path.exists("video_atual.mp4"):
            if video_captura:
                video_captura.release()
            os.remove("video_atual.mp4")
            
        # Faz o download salvando com um nome padrão fixo
        stream.download(filename="video_atual.mp4")
        
        # Abre o arquivo baixado usando o OpenCV
        video_captura = cv2.VideoCapture("video_atual.mp4")
        video_carregado = True
        
        print(f"Vídeo '{titulo_atual}' pronto para transmissão!")
        return jsonify({"status": "sucesso", "mensagem": f"Tocando: {titulo_atual}"})
        
    except Exception as e:
        print(f"Falha ao processar o download do YouTube: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro no download: {str(e)}"}), 500

@app.route('/proximo-frame', methods=['GET'])
def proximo_frame():
    global video_captura, video_carregado
    
    if not video_carregado or not video_captura:
        return jsonify({"erro": "Nenhum vídeo ativo. Cole um link primeiro."}), 400
        
    # Lê o frame atual do arquivo de vídeo
    sucesso, frame = video_captura.read()
    
    # Se o vídeo chegou ao fim, reinicia do frame zero (Loop infinito)
    if not sucesso:
        video_captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
        sucesso, frame = video_captura.read()
        if not sucesso:
            return jsonify({"erro": "Não foi possível ler o frame do vídeo"}), 500
            
    # Redimensiona a imagem do frame para a matriz de baixa resolução (32x24)
    frame_redimensionado = cv2.resize(frame, (LARGURA, ALTURA))
    
    # Converte de BGR para RGB
    frame_rgb = cv2.cvtColor(frame_redimensionado, cv2.COLOR_BGR2RGB)
    
    # Monta a lista linear de inteiros compacta: [R, G, B, R, G, B...]
    lista_pixels = []
    for y in range(ALTURA):
        for x in range(LARGURA):
            r, g, b = frame_rgb[y, x]
            lista_pixels.append(int(r))
            lista_pixels.append(int(g))
            lista_pixels.append(int(b))
            
    return jsonify({
        "largura": LARGURA,
        "altura": ALTURA,
        "pixels": lista_pixels
    })

if __name__ == '__main__':
    # Inicializa o servidor Flask
    print("Servidor Python da TV iniciado com sucesso!")
    app.run(host='0.0.0.0', port=5000)
    