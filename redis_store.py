import json
import redis
import streamlit as st

# r = redis.Redis(host='localhost', port=6379, db=0) Local ENV

r = redis.Redis(
  host='redis-15349.c294.ap-northeast-1-2.ec2.cloud.redislabs.com',
  port=15349,
  password= st.secrets["redisdbpw"])

def store_interaction(user_id, interaction_type, interaction_data):
    interaction_data = {"type": interaction_type, "content": interaction_data}
    interaction_json = json.dumps(interaction_data)
    r.lpush(user_id, interaction_json)

def fetch_last_n_interactions(user_id, n):
    interactions = r.lrange(user_id, 0, n-1)
    return interactions

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True
