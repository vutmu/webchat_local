import base64
import os
import requests

from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(file, path):
    if file.filename == '':
        return {'status': 'No selected file'}
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(path, filename))
        return path + filename


def download_to_imgbb(pathfile):
    apiKey = os.environ['IMGBB_API_KEY']
    fileLocation = pathfile
    with open(fileLocation, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": apiKey,
            "image": base64.b64encode(file.read()),
        }
        res = requests.post(url, payload)

    if res.status_code == 200:
        data = res.json()
        data = data['data']
        ref = data['url']
        thumb = data['thumb']
        thumb = thumb['url']
        return {'avatar': thumb, 'full_avatar': ref}
    else:
        print("ERROR")
        print("Server Response: " + str(res.status_code))


def imgrout(file, path):
    pathfile = upload_file(file, path)
    ref = download_to_imgbb(pathfile)
    os.remove(pathfile)
    return ref
