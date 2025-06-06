# This program makes a database of backgammon positions from a directory of
# position files. This is done by converting backgammon position with tags into
# a graph, serializing the graph in binary, and writing it to a new file in the
# output directory

import os
import sys
import pickle
import convert_to_graph

def main():
    # Example command: "python mk_database.py positions output
    if len(sys.argv) > 2:
        directory = sys.argv[1]
        out_directory = sys.argv[2]
        full_directory = r"\Users\aadam\Documents\blunderbase\\" + directory
        full_out_directory = r"\Users\aadam\Documents\blunderbase\\" + out_directory
        for filename in os.listdir(full_directory):
            # iterate through all files in the position directory and convert the positions into graph format
            file_path = os.path.join(full_directory, filename)
            if os.path.isfile(file_path):
                pk_filename = full_out_directory + r"\\" + filename[:-3] + "pk"
                with open(pk_filename, 'wb') as pk_f:
                    pickle.dump(convert_to_graph.get(file_path, True), pk_f)
    else:
        print("ERROR: need 2 arguments");

if __name__ == "__main__":
    main()
