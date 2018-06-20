import tensorflow as tf
import numpy as np
from settings import Settings
import smallnet_architecture as net
import sys
import os, time, re

def train(run, settings):
    print("########################")
    print("#     Build Network    #")
    print("########################")
    loader = settings.loader
    network = net.Smallnet(settings)

    print("########################")
    print("#       Training       #")
    print("########################")
    with tf.Session() as session:
        summary_writer = tf.summary.FileWriter(settings.summary_path + str(run), session.graph)
        saver = tf.train.Saver(max_to_keep=10000)

        # check if run already exits: if so continue run
        if os.path.isdir("./stored_weights/"+str(run)):
            print("[Info] Stored weights for run detected.")
            print("[Info] Loading weights...")
            saver.restore(session, tf.train.latest_checkpoint('./stored_weights/'+str(run)))
        else:
            session.run(tf.global_variables_initializer())

        # Initialize the global_step tensor
        tf.train.global_step(session, network.global_step)
        print(" Epoch | Val Acc | Avg Tr Acc | Avg. Loss | Avg. CrossEntropy | Avg. L1 Penalty |  Time")
        print("-------+---------+------------+-----------+-------------------+-----------------+--------")
        for epoch in range(settings.epochs):
            t = time.time()

            ## Training
            losses = []
            penalties = []
            cross_entropies = []
            accuracies = []
            for train_inputs, train_labels in loader.get_training_batch(settings.batch_size):
                _global_step, _xentropy, _penalty, _logits, _summaries, _, _loss, _accuracy = session.run(
                    [network.global_step, network.xentropy, network.penalty, network.logits, network.summaries,
                    network.update, network.loss, network.accuracy],
                    feed_dict={
                        network.inputs:train_inputs,
                        network.labels:train_labels,
                        network.learning_rate: settings.l_rate
                })
                losses.append(_loss)
                penalties.append(_penalty)
                cross_entropies.append(_xentropy)
                accuracies.append(_accuracy)
                # write summaries
                summary_writer.add_summary(_summaries, tf.train.global_step(session, network.global_step))

            # validation
            val_inputs, val_labels = next(loader.get_validation_batch(0))
            val_acc, _ = session.run([network.accuracy, network.loss],
                feed_dict={
                    network.inputs:val_inputs,
                    network.labels:val_labels,
                    network.learning_rate: 0.001})

            # Save model
            saver.save(session, os.path.join("./stored_weights", str(run), "small_weights"), global_step=_global_step)

            #Printing Information
            t = time.time() - t
            minutes, seconds = divmod(t, 60)
            avg_loss = np.average(losses)
            avg_penalty = np.average(penalties)
            avg_cross_entropy = np.average(cross_entropies)
            avg_tr_acc = np.average(accuracies)
            #print(" Epoch | Val Acc | Avg TrAcc | Avg. CrossEntropy | Avg. L1 Penalty")
            print(" #{0: 3d}  | {1: .3f}  |  {2: .3f}   |  {3: .3f}   |      {4: .3f}       |     {5: .3f}      | {6: .0f}m{7: .2f}s".format(epoch + 1, val_acc, avg_tr_acc, avg_loss, avg_cross_entropy, avg_penalty, minutes, seconds))
            print("-------+---------+-----------+-----------+-------------------+-----------------+--------")

def extract_number(f):
    s = re.findall(r"\d+$",f)
    return (int(s[0]) if s else -1,f)

def main(argv):
    settings = Settings()
    run = -1
    if len(argv) == 0:
        files = [d.name for d in os.scandir(settings.summary_path)]
        run = str(int(max(files,key=extract_number)) + 1)
    else:
        run = argv[0]
    if os.path.isdir(settings.summary_path + run):
        print('[Attention] The specified run already exists!')
        sys.exit()

    train(run, settings)

if __name__ == "__main__":
   main(sys.argv[1:])
