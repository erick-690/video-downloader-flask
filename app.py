import os
import uuid
import logging

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='docs')
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

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
        temp_output_path_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_filename}.%(ext)s')

        # Obtém o conteúdo dos cookies da variável de ambiente
        cookies_content = os.environ.get('YTDL_COOKIES')
            # Se houver cookies, crie um arquivo temporário para eles
        cookie_file_path = None
        if cookies_content:
            cookie_file_path = os.path.join(DOWNLOAD_FOLDER, f'{uuid.uuid4()}_cookies.txt')
            with open(cookie_file_path, 'w') as f:
                f.write(cookies_content)
            app.logger.debug(f"Cookies lidos da variável de ambiente e salvos em: {cookie_file_path}")
        else:
            app.logger.warning("Variável de ambiente YTDL_COOKIES não encontrada ou vazia. Tentando sem cookies.")


        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': temp_output_path_template,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'retries': 5,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'verbose': True,
        }

        # Adiciona a opção de cookies se o arquivo foi criado
        if cookie_file_path:
            ydl_opts['cookiefile'] = cookie_file_path
            app.logger.debug(f"Adicionando cookiefile: {cookie_file_path} às opções do yt-dlp")


        file_path = None
        download_filename = "video_baixado.mp4"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            app.logger.info(f"Iniciando extração e download com yt-dlp para: {video_url}")
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

            if 'title' in info and 'ext' in info:
                sanitized_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                download_filename = f"{sanitized_title}.{info['ext']}"
                if len(download_filename) > 150:
                    download_filename = download_filename[:145] + '.' + info['ext']

        if file_path and os.path.exists(file_path):
            app.logger.info(f"Download concluído. Enviando arquivo: {download_filename}")
            mimetype = 'video/mp4'
            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_filename,
                mimetype=mimetype
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
    finally:
        # Limpa o arquivo de cookies temporário
        if cookie_file_path and os.path.exists(cookie_file_path):
            try:
                os.remove(cookie_file_path)
                app.logger.debug(f"Arquivo de cookies temporário removido: {cookie_file_path}")
            except Exception as e:
                app.logger.warning(f"Não foi possível remover o arquivo de cookies temporário {cookie_file_path}: {e}")


@app.route('/')
def index():
    app.logger.info("Servindo index.html")
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    app.logger.info(f"Servindo arquivo estático: {path}")
    return app.send_static_file(path)

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'production':
        app.logger.info("Ambiente de produção detectado. Gunicorn irá iniciar o aplicativo.")
    else:
        app.logger.info("Ambiente de desenvolvimento detectado. Iniciando servidor Flask localmente.")
        app.run(debug=True, host='0.0.0.0')