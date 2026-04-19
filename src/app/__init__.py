from normaldb import SchemaBuilder
from flask import Flask, render_template, request, url_for, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("./index.html")


@app.route("/normalize", methods=["POST"])
def normalize():
    try:
        data = request.get_json(silent=True)
        print("Received data:", data)

        if data is None:
            return (
                jsonify({"success": False, "error": "No JSON body received."}),
                400,
            )

        attributes = set(data["attributes"])
        keys = [set(key) for key in data["keys"]]
        functional_deps = [
            (set(lhs), set(rhs)) for lhs, rhs in data["functional_deps"]
        ]

        print(f"Attributes: {attributes}")
        print(f"Keys: {keys}")
        print(f"FDs: {functional_deps}")

        schema_builder = SchemaBuilder(
            attributes=attributes, keys=keys, functional_deps=functional_deps
        )
        result = schema_builder.synthesised_schema()

        print("Result from SchemaBuilder:", result)

        # Convert result to JSON-serializable format
        if result:
            relations = [
                {
                    "name": f"R{i+1}",
                    "attributes": (
                        list(relation)
                        if hasattr(relation, "__iter__")
                        else [relation]
                    ),
                }
                for i, relation in enumerate(result)
            ]
            return jsonify(
                {
                    "success": True,
                    "relations": relations,
                    "summary": (
                        f"Schema successfully decomposed into {len(relations)} "
                        f"relations in 3NF",
                    ),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": (
                            "Decomposition returned empty result. Check your "
                            "input."
                        ),
                    }
                ),
                400,
            )

    except Exception as error:
        print("Normalization error:", error)
        import traceback

        traceback.print_exc()
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Normalization failed: {str(error)}",
                }
            ),
            500,
        )
