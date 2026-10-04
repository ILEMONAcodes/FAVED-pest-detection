import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Lock

import numpy as np
from unified_pipeline import UnifiedDetector, annotate_image, classify_disease_name
from knowledge_base import (
	load_markdown_kb,
	recommendation_from_knowledge,
	merge_recommendation_with_knowledge,
)


class Value:
	def __init__(self, value):
		self.value = value

	def item(self):
		return self.value


class Coordinates:
	def __init__(self, values):
		self.values = values

	def tolist(self):
		return self.values


class FakeBox:
	def __init__(self, class_id, confidence, xyxy):
		self.cls = [Value(class_id)]
		self.conf = [Value(confidence)]
		self.xyxy = [Coordinates(xyxy)]


class FakeResult:
	orig_shape = (100, 100)

	def __init__(self, boxes):
		self.boxes = boxes


class FakeModel:
	def __init__(self, names, boxes, barrier):
		self.names = names
		self.boxes = boxes
		self.barrier = barrier
		self.calls = 0

	def predict(self, *_args, **_kwargs):
		self.calls += 1
		self.barrier.wait(timeout=3)
		return [FakeResult(self.boxes)]


class UnifiedPipelineTests(unittest.TestCase):
	def test_markdown_knowledge_base_frontmatter_is_loaded(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "army_worm.md"
			path.write_text(
				"---\ncrop: maize\nlabel_key: army_worm\nstatus: draft\n---\n\nGuidance text.\n",
				encoding="utf-8",
			)

			entries = load_markdown_kb(Path(directory))

		self.assertEqual(entries["army_worm"]["metadata"]["crop"], "maize")
		self.assertEqual(entries["army_worm"]["text"], "Guidance text.")

	def test_markdown_knowledge_produces_specific_advice_without_llm(self):
		finding = {"label": "Cocoa Mirid"}
		entry = {
			"metadata": {"scientific_name": "Sahlbergella singularis"},
			"text": (
				"## Identification\nMirids are sap-sucking bugs.\n\n"
				"## Damage and symptoms\nFeeding leaves dark spots on pods.\n\n"
				"## Conditions that favour it\nDense shade and poor pruning favour mirids.\n\n"
				"## Cultural and prevention practices\nPrune chupons and remove mummified pods.\n\n"
				"## Biological and low-risk controls\nProtect weaver ants where possible.\n\n"
				"## When to contact an extension officer\nContact an officer if many pods are damaged.\n"
			),
		}

		result = recommendation_from_knowledge(finding, entry)

		self.assertIn("sap-sucking bugs", result["description"])
		self.assertIn("Dense shade", result["cause"])
		self.assertTrue(any("Prune chupons" in step for step in result["steps"]))
		self.assertTrue(any("Protect weaver ants" in step for step in result["prevention"]))
		self.assertEqual(result["pathogen"], "Sahlbergella singularis")
		self.assertIn("Contact an officer", result["steps"][-1])

	def test_generic_llm_fallback_is_filled_from_matching_pest_file(self):
		finding = {"label": "Cocoa Mirid", "label_key": "cocoa_mirid"}
		entry = {
			"metadata": {"scientific_name": "Sahlbergella singularis"},
			"text": (
				"## Identification\nMirids are sap-sucking bugs.\n"
				"## Conditions that favour it\nDense shade favours mirids.\n"
				"## Cultural and prevention practices\nPrune chupons and clean the farm.\n"
			),
		}
		recommendation = {
			"description": "We couldn't generate a detailed recommendation right now.",
			"cause": "",
			"steps": ["Please consult your local agricultural extension officer for guidance."],
			"prevention": [],
		}

		result = merge_recommendation_with_knowledge(recommendation, [finding], {"cocoa_mirid": entry})

		self.assertIn("sap-sucking bugs", result["description"])
		self.assertIn("Dense shade", result["cause"])
		self.assertIn("Prune chupons", result["steps"][0])
		self.assertEqual(result["pathogen"], "Sahlbergella singularis")

	def test_verified_disease_labels_map_to_registry(self):
		self.assertEqual(
			classify_disease_name("Cocoa BlackPod"),
			("disease", "cocoa", "cocoa_black_pod"),
		)
		self.assertEqual(
			classify_disease_name("Cocoa Mirid"),
			("pest", "cocoa", "cocoa_mirid"),
		)
		self.assertEqual(
			classify_disease_name("Maize Gray Leaf Spot"),
			("disease", "maize", "maize_gray_leaf_spot"),
		)

	def test_models_run_together_and_mirid_evidence_is_merged(self):
		barrier = Barrier(2)
		detector = UnifiedDetector.__new__(UnifiedDetector)
		detector.pest_model = FakeModel(
			{7: "Mirid-bug", 3: "Army worm"},
			[
				FakeBox(7, 0.82, [10, 10, 30, 30]),
				FakeBox(3, 0.77, [40, 40, 65, 65]),
			],
			barrier,
		)
		detector.disease_model = FakeModel(
			{3: "Cocoa Mirid", 5: "Maize Gray Leaf Spot"},
			[
				FakeBox(3, 0.72, [11, 11, 29, 29]),
				FakeBox(5, 0.91, [45, 45, 70, 70]),
			],
			barrier,
		)
		detector.pest_conf = 0.25
		detector.disease_conf = 0.5
		detector.imgsz = 640
		detector.review_conf = 0.45
		detector._pest_lock = Lock()
		detector._disease_lock = Lock()

		result = detector.analyze(object())

		mirid = next(item for item in result["findings"] if item["label_key"] == "cocoa_mirid")
		self.assertEqual(mirid["type"], "pest")
		self.assertEqual(mirid["count"], 2)
		self.assertEqual(mirid["evidence"], ["disease_model", "pest_model"])
		self.assertEqual(result["status"], "pest_and_disease")
		self.assertEqual(result["n_pests"], 2)
		self.assertEqual(result["n_diseases"], 1)

	def test_empty_inference_is_marked_unrecognized(self):
		detector = UnifiedDetector.__new__(UnifiedDetector)
		detector.pest_model = FakeModel({0: "Army worm"}, [], Barrier(1))
		detector.disease_model = None
		detector.pest_conf = 0.25
		detector.disease_conf = 0.5
		detector.imgsz = 640
		detector.review_conf = 0.45
		detector._pest_lock = Lock()
		detector._disease_lock = Lock()

		result = detector.analyze(object())

		self.assertFalse(result["recognized"])
		self.assertEqual(result["status"], "no_detection")

	def test_crop_mode_skips_pest_model(self):
		detector = self.make_detector()

		result = detector.analyze(object(), mode="crop")

		self.assertEqual(detector.pest_model.calls, 0)
		self.assertEqual(detector.disease_model.calls, 1)
		self.assertEqual(result["mode"], "crop")
		self.assertEqual(result["n_pests"], 0)

	def test_pest_mode_skips_disease_model(self):
		detector = self.make_detector()

		result = detector.analyze(object(), mode="pest")

		self.assertEqual(detector.pest_model.calls, 1)
		self.assertEqual(detector.disease_model.calls, 0)
		self.assertEqual(result["mode"], "pest")
		self.assertEqual(result["n_diseases"], 0)

	def make_detector(self):
		detector = UnifiedDetector.__new__(UnifiedDetector)
		detector.pest_model = FakeModel({0: "Army worm"}, [], Barrier(1))
		detector.disease_model = FakeModel({0: "Maize Common Rust"}, [], Barrier(1))
		detector.pest_conf = 0.25
		detector.disease_conf = 0.5
		detector.imgsz = 640
		detector.review_conf = 0.45
		detector._pest_lock = Lock()
		detector._disease_lock = Lock()
		return detector

	def test_annotation_draws_on_a_copy_of_the_input(self):
		image = np.zeros((32, 32, 3), dtype=np.uint8)
		detections = [{
			"bbox_xyxy": [2, 2, 20, 20],
			"type": "pest",
			"label": "Army worm",
			"confidence": 0.9,
		}]

		annotated = annotate_image(image, detections)

		self.assertTrue(np.array_equal(image, np.zeros_like(image)))
		self.assertFalse(np.array_equal(annotated, image))


if __name__ == "__main__":
	unittest.main()