import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)
from datasets import Dataset, DatasetDict
import numpy as np


def train_model(output_dir="src/model/trained_model/"):
    # Data preparation
    transform = transforms.Compose(
        [transforms.Grayscale(num_output_channels=3), transforms.ToTensor()]
    )
    train_data = datasets.MNIST(
        root="data/", train=True, download=True, transform=transform
    )

    # Prepare the dataset for Hugging Face's Dataset API
    dataset_dict = {
        "image": [train_data[i][0].numpy() for i in range(len(train_data))],
        "label": [int(train_data[i][1]) for i in range(len(train_data))],
    }
    dataset = Dataset.from_dict(dataset_dict)

    # Split dataset into train and test
    dataset = dataset.train_test_split(test_size=0.2, seed=42)
    train_dataset = dataset["train"]
    test_dataset = dataset["test"]

    # Ensure proper conversion during mapping
    def preprocess_data(example):
        return {
            "image": torch.tensor(example["image"], dtype=torch.float32),
            "label": torch.tensor(example["label"], dtype=torch.long),
        }

    train_dataset = train_dataset.map(preprocess_data)
    test_dataset = test_dataset.map(preprocess_data)

    # Initialize the processor and model
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained(
        "microsoft/trocr-base-handwritten"
    )

    # Adjust model config for MNIST
    model.config.decoder.vocab_size = 11  # 10 digits + <eos> token
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.eos_token_id = processor.tokenizer.eos_token_id
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.max_length = 5  # Ensure the decoder output has a fixed sequence length

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        eval_strategy="steps",
        learning_rate=5e-5,
        per_device_train_batch_size=16,
        num_train_epochs=5,
        save_steps=500,
        save_total_limit=2,
        predict_with_generate=True,
        logging_dir="logs",
        logging_steps=10,
    )

    # Define a data collator for preprocessing images and labels
    def data_collator(features):
        images = torch.stack([f["image"] for f in features])
        labels = torch.tensor([f["label"] for f in features])

        pixel_values = processor(images=images, return_tensors="pt").pixel_values

        # Convert labels to sequences and pad
        decoder_input_ids = [
            torch.tensor([label.item(), model.config.eos_token_id], dtype=torch.long)
            for label in labels
        ]
        decoder_input_ids = pad_sequence(
            decoder_input_ids,
            batch_first=True,
            padding_value=model.config.pad_token_id,
        )

        return {
            "pixel_values": pixel_values,
            "labels": decoder_input_ids,
        }

    # Debugging dataset shapes
    print("Train dataset example:", train_dataset[0])
    print("Test dataset example:", test_dataset[0])

    # Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        data_collator=data_collator,
    )

    trainer.train()

    # Save the trained model
    model.save_pretrained(output_dir)
    processor.save_pretrained(output_dir)
    print(f"Model and processor saved to {output_dir}")


if __name__ == "__main__":
    train_model()
