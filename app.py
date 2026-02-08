from flask import Flask, request, send_file, render_template, jsonify
import youtube_dl
import os
from pathlib import Path

app = Flask(__name__, template_folder='templates', static_folder='static')

# Create downloads directory if it doesn't exist
DOWNLOADS_DIR = 'downloads'
Path(DOWNLOADS_DIR).mkdir(exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/formats', methods=['POST'])
def get_formats():
    """Get available formats for a YouTube video"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required!'}), 400
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Filter and format the response
            available_formats = []
            seen_format_ids = set()
            
            for fmt in formats:
                format_id = fmt.get('format_id')
                format_note = fmt.get('format_note', 'Unknown')
                ext = fmt.get('ext', 'unknown')
                fps = fmt.get('fps', 0)
                
                # Avoid duplicates
                if format_id not in seen_format_ids:
                    if fmt.get('vcodec') != 'none':  # Video format
                        height = fmt.get('height', 0)
                        if height:
                            available_formats.append({
                                'format_id': format_id,
                                'description': f'{height}p - {format_note} ({ext})',
                                'type': 'video',
                                'ext': ext
                            })
                    elif fmt.get('acodec') != 'none':  # Audio format
                        abr = fmt.get('abr', 0)
                        if abr:
                            available_formats.append({
                                'format_id': format_id,
                                'description': f'Audio {abr}kbps ({ext})',
                                'type': 'audio',
                                'ext': ext
                            })
                    
                    seen_format_ids.add(format_id)
            
            # Add preset options
            presets = [
                {'format_id': 'best[ext=mp4]', 'description': 'Best MP4 Video', 'type': 'video', 'ext': 'mp4'},
                {'format_id': 'best[ext=mkv]', 'description': 'Best MKV Video', 'type': 'video', 'ext': 'mkv'},
                {'format_id': 'bestaudio[ext=m4a]', 'description': 'Best Audio (M4A)', 'type': 'audio', 'ext': 'm4a'},
                {'format_id': 'bestaudio[ext=mp3]', 'description': 'Best Audio (MP3)', 'type': 'audio', 'ext': 'mp3'},
            ]
            
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'presets': presets,
                'formats': available_formats[:20]  # Limit to top 20 formats
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    """Download YouTube video in specified format"""
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id', 'best')
    
    if not url:
        return jsonify({'error': 'URL is required!'}), 400
    
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        return jsonify({
            'success': True,
            'message': 'Download completed!',
            'filename': os.path.basename(filename)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)