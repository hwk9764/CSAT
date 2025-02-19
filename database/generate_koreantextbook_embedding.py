import os
import sys
import torch
import random
import logging
import argparse
import numpy as np
from tqdm import tqdm
from datasets import load_from_disk, load_dataset

sys.path.append("../")
from model.bm25 import BM25SModel
from transformers import AutoTokenizer

LOGGER = logging.getLogger()


def init_logging():
    LOGGER.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s: [ %(message)s ]", "%m/%d/%Y %I:%M:%S %p")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    LOGGER.addHandler(console)


def seed_everything(args):
    random.seed(args.random_seed)
    np.random.seed(args.random_seed)
    os.environ["PYTHONHASHSEED"] = str(args.random_seed)
    torch.manual_seed(args.random_seed)
    torch.cuda.manual_seed(args.random_seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def main(args):
    init_logging()
    seed_everything(args)

    LOGGER.info("*** Building Vector Database ***")
    tokenizer = AutoTokenizer.from_pretrained("beomi/Solar-Ko-Recovery-11B")

    print(f">>> Load data")
    # dataset = load_dataset("maywell/korean_textbooks", "tiny-textbooks")
    # dataset.save_to_disk("../resources/koreanTextbook")
    dataset = load_from_disk("../resources/koreanTextbook")
    print(dataset)
    title_lst = []
    txt_lst = []
    for i, d in tqdm(enumerate(dataset["train"]), total=len(dataset["train"])):
        instructions = d["text"]
        title_lst.append(i)
        txt_lst.append("\n".join([instructions]))
    print(title_lst[:2])
    print(txt_lst[:2])
    print(f">>> Total number of passages: {len(txt_lst)}")

    #### Train BM 25 ####
    print(">>> Train BM 25")
    if args.train_bm25:
        bm25_model = BM25SModel(tokenizer=tokenizer)
        bm25_model.build_bm25_model(text=txt_lst, title=None, path=args.save_path)


if __name__ == "__main__":
    # fmt: off
    parser = argparse.ArgumentParser(description="Build vector database with wiki text")
    parser.add_argument("--save_path", type=str, default="./bm25_model_textbook", help="Save directory of faiss index")
    parser.add_argument("--save_context", action="store_true", default=True, help="Save text and title with faiss index")
    parser.add_argument("--train_bm25", action="store_true", default=True, help="Train bm25 with the same corpus")
    parser.add_argument("--num_sent", type=int, default=5, help="Number of sentences consisting of a wiki chunk")
    parser.add_argument("--overlap", type=int, default=0, help="Number of overlapping sentences between consecutive chunks")
    parser.add_argument("--pooler", default="cls", type=str, help="Pooler type : {pooler_output|cls|mean|max}")
    parser.add_argument("--max_length", type=int, default=512, help="Max length for encoder model")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser.add_argument("--cpu_workers", type=int, default=50, required=False, help="Number of cpu cores used in chunking wiki text")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", type=str, help="Choose a type of device for training")
    parser.add_argument("--random_seed", default=104, type=int, help="Random seed")
    # fmt: on
    args = parser.parse_args()

    main(args)
