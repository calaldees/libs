"""
Rather than duplicating entire chunks of ini files
have a master file and recreate the differnece
"""
import re

#-------------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------------

version = "0.0"


#-------------------------------------------------------------------------------
# Merge INI
#-------------------------------------------------------------------------------
ini_group = None


def make_ini(master_filename, diff_filename, destination_filename):

    def split_line(line):
        try:
            key, value = tuple(line.split('='))
            key = key.strip()
            return (key, value)
        except ValueError:
            return (None, None)

    def update_ini_group(line):
        try:
            global ini_group
            ini_group = re.match('\[(.*)\]', line).group(1)
            return True
        except:  # IndexError, AttributeError
            return False

    # Extract diff from inidiff
    diff_data = {}
    with open(diff_filename, 'r') as diff_file:
        for line in diff_file:
            #print(line)
            try:
                if update_ini_group(line):
                    diff_data[ini_group] = {}
            except:  # IndexError, AttributeError
                pass
            key, value = split_line(line)
            diff_data[ini_group][key] = value

    with open(master_filename, 'r') as master:
        with open(destination_filename, 'w') as destination:
            for line in master:
                update_ini_group(line)
                key, value = split_line(line)
                if key and key in diff_data.get(ini_group,{}):
                    line = '{0} = {1}'.format(key, diff_data[ini_group][key])
                destination.write(line)


def get_ini_to_make():
    #ls *.inidiff
    return ['test', 'production']  # temp for now


#-------------------------------------------------------------------------------
# Command Line
#-------------------------------------------------------------------------------

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="""Make the ini files""",
        epilog=""""""
    )
    parser.add_argument('source', help='')
    parser.add_argument('diff', help='diff')
    parser.add_argument('destination', help='destination ini filename')
    parser.add_argument('--version', action='version', version=version)

    args = vars(parser.parse_args())
    #args['destination'] = args['destination'] or f'{args["ini"]}.ini'
    #args['diff'] = args['diff'] or f'{args["ini"]}.inidiff'

    return args


def main():
    args = get_args()
    make_ini(args['source'], args['diff'], args['destination'])


if __name__ == "__main__":
    main()
