import os
from dotenv import load_dotenv

load_dotenv()

SECRET = os.environ["SERVER_KEY"]  # server-to-server secret to prevent external abuse
SIMULATOR_MODEL_NAME = (
    "text-davinci-003"  # only this model supports logprobs, which is needed for scoring
)
MAX_CONCURRENT = 20  # maximum number of concurrent OpenAI calls

from neuron_explainer.activations.activations import (
    ActivationRecord,
)
from neuron_explainer.explanations.calibrated_simulator import (
    UncalibratedNeuronSimulator,
)
from neuron_explainer.explanations.prompt_builder import PromptFormat
from neuron_explainer.explanations.scoring import simulate_and_score
from neuron_explainer.explanations.simulator import ExplanationNeuronSimulator
from flask import Flask, jsonify, request

app = Flask(__name__)

print("loading")


@app.route("/score", methods=["POST"])
async def create():
    data = request.get_json()
    if "explanation" not in data or "secret" not in data or "activations" not in data:
        print("invalid")
        return jsonify(
            {
                "error": "Invalid",
            }
        )

    secret = data["secret"]
    if secret != SECRET:
        print("forbidden")
        return jsonify(
            {
                "error": "Forbidden",
            }
        )

    explanation = data["explanation"]
    print(explanation)

    # make correct format of activationRecords
    activationRecords = []
    for activation in data["activations"]:
        # print(len(activation["tokens"]))
        # print(len(activation["values"]))
        activationRecords.append(
            ActivationRecord(
                tokens=activation["tokens"], activations=activation["values"]
            )
        )

    # Simulate and score the explanation.
    simulator = UncalibratedNeuronSimulator(
        ExplanationNeuronSimulator(
            SIMULATOR_MODEL_NAME,
            explanation,
            max_concurrent=MAX_CONCURRENT,
            prompt_format=PromptFormat.INSTRUCTION_FOLLOWING,
        )
    )
    scored_simulation = await simulate_and_score(simulator, activationRecords)

    print(f"score={scored_simulation.get_preferred_score():.2f}")
    return jsonify(
        {
            "score": scored_simulation.get_preferred_score(),
            "simulations": scored_simulation.scored_sequence_simulations,
        }
    )


if __name__ == "__main__":
    app.run()
