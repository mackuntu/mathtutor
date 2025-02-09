import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# Initialize processor with custom vocabulary
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")

# Initialize model
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

# Set beam search parameters
model.config.max_length = 5
model.config.early_stopping = True
model.config.no_repeat_ngram_size = 3
model.config.length_penalty = 2.0
model.config.num_beams = 4

# Save model and processor
model.save_pretrained("src/model/trained_model")
processor.save_pretrained("src/model/trained_model")

print("Model and processor saved successfully to src/model/trained_model")
