from flask import Flask, request, send_file
import youtube_dl

app = Flask(__name__)

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return "URL is required!", 400

    # Define options for youtube-dl
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)