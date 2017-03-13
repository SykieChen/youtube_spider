# coding=utf-8
import requests
import json
import configparser
import unicodecsv as csv
import codecs


def read_config():
	global key, video_id, proxy
	cfg = configparser.ConfigParser()
	cfg.read("config.ini")
	key = cfg.get("API", "key")
	video_id = cfg.get("Request", "video_id")
	proxy = {
		'http' : 'http://' + cfg.get("Proxy", "server") + ':' + cfg.get("Proxy", "port"),
		'https' : 'https://' + cfg.get("Proxy", "server") + ':' + cfg.get("Proxy", "port")
	}


def get_top_comments():
	params = {
		'key' : key,
		'part' : 'snippet',
		'videoId' : video_id,
		'order' : 'time',
		'pageToken' : ''
	}
	top_comments = []
	url = 'https://www.googleapis.com/youtube/v3/commentThreads'
	while 1:
		response = requests.get(url, params=params, proxies=proxy)
		json_data = json.loads(response.text)
		top_comments += json_data['items']
		print(len(top_comments), 'top level comments collected',)
		if 'nextPageToken' in json_data.keys() :
			params['pageToken'] = json_data["nextPageToken"]
		else:
			break
	return top_comments

def get_replies(top_comments):
	params = {
		'key' : key,
		'part' : 'snippet',
		'parentId' : '',
		'pageToken' : ''
	}
	url = 'https://www.googleapis.com/youtube/v3/comments'
	replies = {}
	for index, comment in enumerate(top_comments):
		print(index, 'of', len(top_comments), ':', end='')
		if comment['snippet']['totalReplyCount'] == 0 :
			print ('no reply')
		else :
			params['parentId'] = comment['id']
			replies[comment['id']] = []
			while 1:
				response = requests.get(url, params=params, proxies=proxy)
				json_data = json.loads(response.text)
				replies[comment['id']] += json_data['items']
				if 'nextPageToken' in json_data.keys() :
					params['pageToken'] = json_data["nextPageToken"]
				else:
					params['pageToken'] = ''
					break
			print(len(replies[comment['id']]), 'replies collected')
	return replies

def write_csv(top_comments, replies):
	headers = [
		'kind',
		'id',
		'parentId',
		'authorDisplayName',
		'textDisplay',
		'textOriginal',
		'likeCount',
		'publishedAt',
		'updatedAt'
	]
	rows = []
	for comment in top_comments:
		rows += [(
			comment['kind']	,
			comment['id']	, 
			'parent'	, 
			comment['snippet']['topLevelComment']['snippet']['authorDisplayName']	, 
			comment['snippet']['topLevelComment']['snippet']['textDisplay']	, 
			comment['snippet']['topLevelComment']['snippet']['textOriginal']	,
			comment['snippet']['topLevelComment']['snippet']['likeCount'],
			comment['snippet']['topLevelComment']['snippet']['publishedAt']	,
			comment['snippet']['topLevelComment']['snippet']['updatedAt']	
		)]
		if comment['snippet']['totalReplyCount'] > 0:
			for reply in replies[comment['id']]:
				rows += [(
					reply['kind']	,
					reply['id']	, 
					reply['snippet']['parentId']	, 
					reply['snippet']['authorDisplayName']	, 
					reply['snippet']['textDisplay']	, 
					reply['snippet']['textOriginal']	,
					reply['snippet']['likeCount'],
					reply['snippet']['publishedAt']	,
					reply['snippet']['updatedAt']	
				)]
	with open(video_id + '.csv', 'wb') as f:
		f.write(codecs.BOM_UTF8)
		f_csv = csv.writer(f)
		f_csv.writerow(headers)
		f_csv.writerows(rows)



	

if __name__ == "__main__":
	read_config()
	print(key, video_id, proxy)
	print('[1/2] Collecting top level comments...')
	top_comments = get_top_comments()
	print('[2/2] Collecting replies top level comments...')
	replies = get_replies(top_comments)
	print('Writing output file...')
	write_csv(top_comments, replies)
	print('Done!')


