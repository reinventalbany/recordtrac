import scribd
from public_records_portal import app
from timeout import timeout


# Set flags:
upload_to_scribd = False 
if app.config['ENVIRONMENT'] != 'LOCAL':
    upload_to_scribd = True


def progress(bytes_sent, bytes_total):
    print("%s of %s (%s%%)" % (bytes_sent, bytes_total, bytes_sent*100/bytes_total))

def upload(file, filename, API_KEY, API_SECRET):
    # Configure the Scribd API.
    scribd.config(API_KEY, API_SECRET)
    doc_id = None
    try:
        # Upload the document from a file.
        doc = scribd.api_user.upload(
            targetfile = file,
            name = filename,
            progress_callback=progress,
            req_buffer = tempfile.TemporaryFile()
            )       
        doc_id = doc.id
        return doc_id
    except scribd.ResponseError, err:
        print 'Scribd failed: code=%d, error=%s' % (err.errno, err.strerror)
        return err.strerror

def get_scribd_download_url(doc_id, record_id = None, API_KEY = None, API_SECRET = None):
	if not API_KEY:
		API_KEY = app.config['SCRIBD_API_KEY']
	if not API_SECRET:
		API_SECRET = app.config['SCRIBD_API_SECRET']
	try:
		scribd.config(API_KEY, API_SECRET)
		doc = scribd.api_user.get(doc_id)
		doc_url = doc.get_download_url()
		if record_id:
			set_scribd_download_url(doc_url, record_id)
		return doc_url
	except:
		return None

def set_scribd_download_url(download_url, record_id):
	record = Record.query.get(record_id)
	record.download_url = download_url
	db.session.add(record)
	db.session.commit()

def scribd_batch_download(): 
	req = Request.query.all()
	for record in req.records:
		if record.download_url:
			urllib.urlretrieve(record.downlaod_url, "saved_records/%s" %(record.filename))

def make_public(doc_id, API_KEY, API_SECRET):
    scribd.config(API_KEY, API_SECRET)
    doc = scribd.api_user.get(doc_id)
    doc.access = 'public'
    doc.save()

def make_private(doc_id, API_KEY, API_SECRET):
    scribd.config(API_KEY, API_SECRET)
    doc = scribd.api_user.get(doc_id)
    doc.access = 'private'
    doc.save()

@timeout(seconds=20)
def upload_file(file): 
# Uploads file to scribd.com and returns doc ID. File can be accessed at scribd.com/doc/id
    if file:
        allowed = allowed_file(file.filename)
        if allowed[0]:
            filename = secure_filename(file.filename)
            if upload_to_scribd: # Check flag
                doc_id = upload(file, filename, app.config['SCRIBD_API_KEY'], app.config['SCRIBD_API_SECRET'])
                return doc_id, filename
            else:
                return '1', filename # Don't need to do real uploads locally
        else:
            return allowed # Returns false and extension
    return None, None