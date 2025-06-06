import sys
import os
import pickle
import shutil
import convert_to_graph

def filter(filter_graph, position):
    if (filter_graph.is_cube != position.is_cube): return False
    if (filter_graph.stage and filter_graph.stage != position.stage): return False
    return filter_help(filter_graph.inner, position)

def filter_help(inner_filter, position):
    print("START")
    if not inner_filter: return True
    inner_filter.print_fil_rec(0)
    position.print_pos()
    print()
    if inner_filter.injunction == "OR":
        return filter_help(inner_filter.left, position) or filter_help(inner_filter.right, position)
    elif inner_filter.injunction == "AND":
        return filter_help(inner_filter.left, position) and filter_help(inner_filter.right, position)
    else:
        for cat in position.categories:
            if cat == inner_filter.category: 
                print("result = true")
                return True
        print("result = false")
        return False

def main():
    # example: python filter.py output filters/filter_A.txt fout
    # where output = directory of positons and fout is output directory of filtered positions
    if len(sys.argv) > 3:
        directory = sys.argv[1]
        filter_file = sys.argv[2]
        out_directory = sys.argv[3]
        full_directory = r"\Users\aadam\Documents\blunderbase\\" + directory
        full_filter_file = r"\Users\aadam\Documents\blunderbase\\" + filter_file
        full_out_directory = r"\Users\aadam\Documents\blunderbase\\" + out_directory
        
        # convert to instance of filter class
        filter_graph = convert_to_graph.get(full_filter_file, False)
        # apply filter to each position in output directory
        filter_graph.print_fil()
        for filename in os.listdir(full_directory):
            file_path = os.path.join(full_directory, filename)
            if os.path.isfile(file_path):
                # Process the file and add to output directory if it passes the filter
                with open(file_path, "rb") as f:
                    print(file_path)
                    position = pickle.load(f)
                print(f"Processing file: {filename}")
                if filter(filter_graph, position):
                    shutil.copy(file_path, full_out_directory)
    else:
        print("ERROR: need 3 arguments");

if __name__ == "__main__":
    main()
