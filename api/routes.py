# api/routes.py

from flask import Blueprint, jsonify, request
from data.repository import MarketRepository

api = Blueprint("api", __name__)


@api.route("/stocks", methods=["GET"])
def get_all_stocks():
    repo = MarketRepository()
    data = repo.fetch_all()
    repo.close()
    return jsonify(data)


@api.route("/stocks/<symbol>", methods=["GET"])
def get_stock(symbol):
    repo = MarketRepository()
    data = repo.fetch_one(symbol.upper())
    repo.close()

    if not data:
        return jsonify({"error": "Stock not found"}), 404

    return jsonify(data)


@api.route("/stocks/top", methods=["GET"])
def get_top_stocks():
    limit = int(request.args.get("limit", 10))

    repo = MarketRepository()
    data = repo.fetch_top(limit)
    repo.close()

    return jsonify(data)


@api.route("/stocks/undervalued", methods=["GET"])
def get_undervalued():
    repo = MarketRepository()
    data = repo.fetch_undervalued()
    repo.close()

    return jsonify(data)


@api.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})