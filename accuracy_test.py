def calculate_accuracy(gt_file, pred_file):
    correct_results = 0
    false_positives = 0
    false_negatives = 0
    total_lines = 0

    with open(gt_file, 'r') as gt, open(pred_file, 'r') as pred:
        for gt_line, pred_line in zip(gt, pred):
            gt_value = int(gt_line.strip())
            pred_value = int(pred_line.strip())

            if gt_value == pred_value:
                correct_results += 1
            elif pred_value == 1:
                false_positives += 1  # If prediction is 1 and ground truth is 0, increment false positives
            else:
                false_negatives += 1  # If prediction is 0 and ground truth is 1, increment false negatives
            
            total_lines += 1

    #accuracy = correct_results / total_lines * 100 if total_lines != 0 else 0
    return correct_results / total_lines * 100, false_positives / total_lines * 100, false_negatives / total_lines * 100

ground_truth_file = 'ground_truth.txt'
predictions_file = 'rounded_output.txt'

accuracy, false_positives, false_negatives = calculate_accuracy(ground_truth_file, predictions_file)

print("Accuracy: {:.2f}%".format(accuracy))
print("False Positives: {:.2f}%".format(false_positives))
print("False Negatives: {:.2f}%".format(false_negatives))