from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from psycopg2.extras import RealDictCursor
import psycopg2
from Api_Sample_Login_V1 import auth
from App_safety import token_authentication


app = Flask(__name__)

app.register_blueprint(auth, url_prefix="/api_authentication")

CORS(app)

#conection string in the same file temporarily

@app.route("/")
def first_page():
    return jsonify(status = "ok")



@app.route("/ABC_ranking", methods=["GET"])
@token_authentication
def abc_ranking():
    try:
        conn = psycopg2.connect(host="127.0.0.1", database="guide", user="postgres", password="1234")
        with conn.cursor() as first_cursor:
            first_cursor.execute("""
                    WITH sum_sales AS (
                        SELECT "StockCode", SUM("Demand"::NUMERIC) AS "TotalDemand", EXTRACT(YEAR FROM "ReleaseDate"::DATE) AS "ReleaseYear"
                        FROM maintest
                        WHERE "DocumentType" = 'O' AND "OrderType" = 'Other'
                        GROUP BY "ReleaseYear", "StockCode"
                        ORDER BY "ReleaseYear" DESC, "TotalDemand" DESC, "StockCode"
                    ),
                    ranked AS (
                        SELECT "StockCode", "TotalDemand", "ReleaseYear",
                        SUM("TotalDemand") OVER(PARTITION BY "ReleaseYear") AS "YearTotal",
                        SUM("TotalDemand") OVER(PARTITION BY "ReleaseYear" ORDER BY "TotalDemand" DESC, "ReleaseYear" DESC) AS "RunningTotal"
                        FROM sum_sales
                    ),
                    percentagerank AS(
                        SELECT "StockCode", "TotalDemand", "RunningTotal"::NUMERIC, "ReleaseYear", "YearTotal",
                        ROUND((("TotalDemand"/"YearTotal")*100), 4) AS "PercentageTotalYear"
                        FROM ranked
                    ),
                    runningpercent AS (
                        SELECT  "StockCode", "TotalDemand", "RunningTotal", "ReleaseYear", "YearTotal", "PercentageTotalYear",
                        SUM("PercentageTotalYear") OVER(PARTITION BY "ReleaseYear" ORDER BY "TotalDemand" DESC, "ReleaseYear" DESC) AS "RunningPercentageYear"
                        FROM percentagerank
                    ),
                    abcrank AS (
                        SELECT  "StockCode", "TotalDemand", "RunningTotal", "ReleaseYear", "YearTotal", "PercentageTotalYear", "RunningPercentageYear",
                        CASE
                            WHEN "RunningPercentageYear" < 30 THEN 'A'
                            WHEN "RunningPercentageYear" < 85 THEN 'B'
                            ELSE 'C' END AS "Ranking"
                        FROM runningpercent
                    )


                    SELECT "StockCode", "ReleaseYear","YearTotal", "TotalDemand","RunningTotal", "PercentageTotalYear", "RunningPercentageYear", "Ranking"
                    FROM abcrank
                    ORDER BY "ReleaseYear" DESC, "TotalDemand" DESC, "StockCode"
                    """)
            result = first_cursor.fetchall()
            return jsonify(result, 200)

        
    except Exception as e:
        Print(e)
        return jsonify({"error:":str(e)}), 500
    finally:
        first_cursor.close()
        conn.close()





@app.route("/stockbreak", methods = ["GET"])
@token_authentication
def stock_break_alert():
    try:
        conn = psycopg2.connect(host = "127.0.0.1", database = "guide", user="postgres", password="1234")
        with conn.cursor() as second_cursor:
            second_cursor.execute("""
                WITH main AS (
                    SELECT "StockCode", "Month", SUM("Demand") AS "SumDemand"
                    FROM maintest
                    GROUP BY "StockCode", "Month"
                    ORDER BY "StockCode" ASC, "Month" ASC
                ),
                calc AS(
                    SELECT "StockCode", "Month", "SumDemand",
                    AVG("SumDemand") OVER(PARTITION BY "StockCode" ORDER BY "StockCode" ASC, "Month" ASC ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS "AvgDemand_5",
                    STDDEV("SumDemand") OVER(PARTITION BY "StockCode" ORDER BY "StockCode" ASC, "Month" ASC ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS "STDDEV_5",
                    MAX("Month") OVER(PARTITION BY "StockCode") AS "MaxMonth"
                    FROM main
                ),
                classification AS(
                    SELECT "StockCode", "Month", "SumDemand", "AvgDemand_5", "STDDEV_5", "MaxMonth",
                    CASE
                        WHEN "Month" = "MaxMonth" THEN 'Y'
                        ELSE 'N' END AS "MaxMonthClass"
                    FROM calc
                )

                SELECT "StockCode", "Month", "SumDemand", "AvgDemand_5"
                FROM classification
                WHERE "MaxMonthClass" = 'Y' AND ("SumDemand" > (ABS("AvgDemand_5")+"STDDEV_5"));""")
            result = second_cursor.fetchall()
            if not result:
                return jsonify(status = "ok"), 200, jsonify("No SKU in stockbreak risk")
            else:
                return jsonify("List of SKUs in risk of StockBreak: ", result, 200)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        second_cursor.close()
        conn.close()




@app.route("/test_auth", methods=["GET", "POST"])
@token_authentication
def test_func():
    print("Test path reached")
    return jsonify("Token Valided successfully"), 200







if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)