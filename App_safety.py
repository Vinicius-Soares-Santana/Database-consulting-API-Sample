from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
import os
from functools import wraps
from Api_Sample_Login_V1 import secret_key


def token_authentication(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get('Authorization', '')        
        if not authorization.startswith('Bearer '):
            return jsonify(error="no token specified or wrong format"), 400

        token = authorization.split(' ', 1)[1]

        try:
            token_payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify(error = "token expired"), 401
        except jwt.InvalidTokenError:
            return jsonify(error="invalid token"), 401

        return f(*args, **kwargs)
    return wrapper



