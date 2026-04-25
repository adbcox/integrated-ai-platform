import sys

def print_labels():
    if len(sys.argv) < 2:
        print("Usage: python print_labels.py label1 label2 ...")
        return
    
    labels = sys.argv[1:]
    for label in labels:
        print(f"Label: {label}")

if __name__ == '__main__':
    print_labels()
