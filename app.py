import os
import uuid
import logging # Importar módulo de logging para depuração

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

# Configuração básica de logging para ver mensagens no console do Render
logging.basicConfig(level=logging.DEBUG) # Mude para logging.DEBUG para mais detalhes

# Informe ao Flask onde estão seus arquivos estáticos
# A pasta 'docs' deve estar no mesmo nível do app.py
app = Flask(__name__, static_folder='docs')
CORS(app) # Habilita CORS para todas as rotas (necessário se frontend e backend em portas diferentes)

DOWNLOAD_FOLDER = 'downloads'

# Cria a pasta de downloads se ela não existir
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Rota para baixar o vídeo
@app.route('/download-video', methods=['POST'])
def download_video():
    data = request.get_json()
    video_url = data.get('url')

    app.logger.info(f"Requisição recebida para URL: {video_url}")

    if not video_url:
        app.logger.warning("URL do vídeo não fornecida.")
        return jsonify({'error': 'URL do vídeo não fornecida'}), 400

    try:
        unique_filename = str(uuid.uuid4())
        # O outtmpl é onde o yt-dlp vai salvar o arquivo localmente.
        temp_output_path_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_filename}.%(ext)s')

        ydl_opts = {
            # Tenta a melhor qualidade de vídeo e áudio separadas E as mescla, ou usa o melhor formato combinado.
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': temp_output_path_template,
            'noplaylist': True,
            'merge_output_format': 'mp4', # Garante que o FFmpeg mescle para MP4
            'retries': 5,
            'postprocessors': [{ # Garante que o FFmpeg está sendo usado para merge
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'verbose': True, # Mantenha o verbose para ver os logs do yt-dlp no console do Render
        }

        file_path = None # Inicializa para garantir que está definido
        download_filename = "video_baixado.mp4" # Nome padrão, caso o título não seja extraído

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            app.logger.info(f"Iniciando extração e download com yt-dlp para: {video_url}")
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info) # Obtém o caminho completo do arquivo salvo
            
            # Tenta obter o título e extensão para um nome de download melhor
            if 'title' in info and 'ext' in info:
                # Remove caracteres inválidos para nomes de arquivo e limita o tamanho
                sanitized_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                download_filename = f"{sanitized_title}.{info['ext']}"
                # Garante que o nome do arquivo não seja muito longo
                if len(download_filename) > 150:
                    download_filename = download_filename[:145] + '.' + info['ext']

        if file_path and os.path.exists(file_path):
            app.logger.info(f"Download concluído. Enviando arquivo: {download_filename}")
            # Define o tipo MIME (pode ser mais específico para outros formatos, mas mp4 é comum)
            mimetype = 'video/mp4' 
            
            # Envia o arquivo com um nome de download específico
            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_filename, # Usa o nome gerado
                mimetype=mimetype # Define o tipo MIME
            )
        else:
            app.logger.error("Arquivo de vídeo não encontrado após o download.")
            return jsonify({'error': 'Arquivo de vídeo não encontrado após o download.'}), 500

    except yt_dlp.DownloadError as e:
        app.logger.error(f"Erro ao baixar o vídeo (yt-dlp.DownloadError): {str(e)}")
        return jsonify({'error': f'Erro ao baixar o vídeo: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Ocorreu um erro inesperado no servidor: {str(e)}", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro inesperado no servidor: {str(e)}'}), 500

# Rota para servir a página inicial (index.html)
@app.route('/')
def index():
    app.logger.info("Servindo index.html")
    return app.send_static_file('index.html')

# Rota para servir outros arquivos estáticos (CSS, JS)
@app.route('/<path:path>')
def static_files(path):
    app.logger.info(f"Servindo arquivo estático: {path}")
    return app.send_static_file(path)

# Bloco de execução principal
if __name__ == '__main__':
    # Use Gunicorn em produção (no Render.com), Werkzeug localmente
    # No Render.com, a variável de ambiente FLASK_ENV será definida como 'production'
    if os.environ.get('FLASK_ENV') == 'production':
        # Gunicorn será executado pelo comando 'gunicorn app:app' no Render.com
        # Não precisamos chamar run() aqui, pois o gunicorn já faz isso.
        # Este bloco é mais para clareza e para evitar que app.run() seja chamado.
        app.logger.info("Ambiente de produção detectado. Gunicorn irá iniciar o aplicativo.")
    else:
        # Para desenvolvimento local, use o servidor embutido do Flask (Werkzeug)
        app.logger.info("Ambiente de desenvolvimento detectado. Iniciando servidor Flask localmente.")
        # Use 0.0.0.0 para ser acessível de outros dispositivos na rede, se necessário
        app.run(debug=True, host='0.0.0.0')