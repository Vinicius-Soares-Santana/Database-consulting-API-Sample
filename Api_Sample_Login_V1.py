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

auth = Blueprint("auth", __name__)

#Temporarily in the same file for testing purposes, but will be moved in the future
#conection string in the same file temporarily
secret_key="sodfni45sfgdfg15drfq34twrtqg"




@auth.route("/register", methods=["POST"])
def register_user():
    try:
        conn = psycopg2.connect(host="127.0.0.1", database="guide", user="postgres", password="1234")
        with conn.cursor() as reg_cursor:

            data = request.get_json()

            username = data.get("username")

            password = data.get("password")

            password_encryption = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            reg_cursor.execute("INSERT INTO user_reg (\"username\", \"password\") VALUES (%s, %s) returning \"username\";", (username, password_encryption))

            conn.commit()

            return jsonify({f"Message {username}:": "User Registered"}), 201
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        reg_cursor.close()
        conn.close()



@auth.route("/login", methods=["POST"])
def login_user():
    try:
        conn = psycopg2.connect(host="127.0.0.1", database="guide", user="postgres", password="1234")
        with conn.cursor() as reg_cursor:

            data = request.get_json()

            username = data.get("username")

            password = data.get("password")


            reg_cursor.execute("SELECT * FROM user_reg WHERE \"username\" = (%s)", (username,))
            result = reg_cursor.fetchone()


            user_id = result[0]
            username_db = result[1]
            password_db = result[2]
            user_role = result[3]




            if bcrypt.checkpw(password.encode("utf-8"), password_db.encode("utf-8")):
                payload = {
                    "user_id": user_id,
                    "username": username_db,
                    "role": user_role,
                    "exp": datetime.now(timezone.utc) + timedelta(days=1)
                }

                token = jwt.encode(payload, secret_key)

                return jsonify(token=token), 200
            
            return jsonify({f"Message:": "Log in has failed"}), 401


            
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        reg_cursor.close()
        conn.close()










@auth.route("/consulting", methods=["GET"])
def user_consulting():
    try:
        conn = psycopg2.connect(host="127.0.0.1", database="guide", user="postgres", password="1234")
        with conn.cursor() as cursor:

            cursor.execute("SELECT \"username\", \"role\" FROM user_reg")
            result = cursor.fetchall()

            return jsonify({"list of users:": result}), 200
    except Exception as e:
        print(e)
        return jasonify({"error:": str(e)}), 500
    finally:
        cursor.close()
        conn.close()






