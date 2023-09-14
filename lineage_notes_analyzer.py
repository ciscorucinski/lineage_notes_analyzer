import re
from typing import Dict

from textwrap import dedent

file_name = 'lineage_notes.txt'
delimiter = '\t'
expected_delimiter_count = 1

errors = dict()

# def check_file_integrity(file):
#     (
#         pd.read_csv(file,
#             delimiter='\t',     # lineage_notes.txt emulates a tsv file; not a csv
#             engine='python',    # on_bad_lines requires 'python'
#             on_bad_lines=lambda line:errors['file'].append(' <<delimiter>> '.join(line))
#             # When pandas can't parse a row correctly, the lambda will receive a delimited list for that specific line
#         )
#     )


def check_data_integrity(file):

    valid_pango = re.compile(r'^X?[ABCDEFGHJKLMNPQRSTUVWYZ]+(?:\.\d+){0,3}$')
    mutation_check = re.compile(r'(\w+:(?:[A-Za-z]?)\d+(?:[A-Za-z])|(?:[A-Za-z]?)\d+(?:[A-Za-z]))')
    alias_of_check = re.compile(r'^X?[ABCDEFGHJKLMNPQRSTUVWYZ]+(?:\.\d+){4,6}$')
    unaliased_check = re.compile(r'.*(X?[ABCDEFGHJKLMNPQRSTUVWYZ]+(?:\.\d+){4,6})')
    valid_basal_epoch = re.compile(r'^[AB]|X\w+')

    with open(file) as lineage_notes:

        for index, line in enumerate(lineage_notes):
            line = line.strip('\n')
            line_number = index + 1
            error_list = []

            tab_count = line.count(delimiter)
            space_count = len(re.findall(r" {2,}", line))

            display = re.sub(r" {2,}", lambda m: f" <<{len(m.group(0))} spaces>> ", line)
            display = ' <<delimiter>> '.join(display.split(delimiter))

            if line:

                if space_count > 0:
                    error_list.append(f'Use of consecutive spaces. Identified {space_count}; expects 0')

                if tab_count > expected_delimiter_count:
                    error_list.append(f'Too many tab characters. Identified {tab_count}; expects {expected_delimiter_count}')
                elif tab_count < expected_delimiter_count:
                    error_list.append(f'Too few tab characters. Identified {tab_count}; expects {expected_delimiter_count}')
                else:
                    if index == 0:
                        continue

                    pango_lineage, full_description = line.split(delimiter)

                    print(line_number, pango_lineage, full_description)

                    # Skip all withdrawn lineages.
                    # TODO check that the description indicates it is withdraw
                    if pango_lineage[0] == '*':
                        continue

                    if not valid_pango.match(pango_lineage):
                        error_list.append(f'Lineage {pango_lineage} is not valid')

                    pango_epoch, *pango_hierarchy = re.split('\.', pango_lineage)

                    # Pango epoch isn't exactly 'A' or 'B' OR a base recombinant like 'XBB'. Therefore, it's re-aliased
                    if not valid_basal_epoch.match(pango_epoch):

                        description_start_regex = re.compile(
                            r'(.* +)?(X?[ABCDEFGHJKLMNPQRSTUVWYZ]+(?:\.\d+){4,})(,?[ \t]?)')

                        if description_match := description_start_regex.search(full_description):

                            unaliased_lineage = description_match.group(2)
                            valid_unalias = True

                            unaliased_group, *unaliased_hierarchy = re.split('\.', unaliased_lineage)

                            if not valid_basal_epoch.match(unaliased_group):
                                valid_unalias = False
                                error_list.append(
                                    f'The unaliased lineage "{unaliased_lineage}" should derive from the "A" or "B" Lineage, or it should come from a recombinant starting with an "X"')
                            else:
                                # TODO else check if the uncompressed pango name matches the unaliased lineage
                                pass


                                # error_list.append(f'''Description should start with "Alias of {unaliased_lineage if valid_unalias else '<<unaliased>>'}, "''')
                            # if not mutation_check.match(str(description_match.group(1))):
                            if not (description_match.group(1) == 'Alias of ' and description_match.group(3) in [', ', '']):
                                error_list.append(f'''Description should start with "Alias of {unaliased_lineage if valid_unalias else '<<unaliased>>'}, "''')
                            # else:
                            #     error_list.append('Description does not start with "Alias of <<unaliased>>, "') # TODO finish message

                        else:
                            error_list.append(f'Could not retrieve the unaliased lineage for {pango_lineage}')
                        # else:
                        #     # TODO could indicate what the predicted unaliased lineage should be
                        #     error_list.append(f'Could not retrieve the unaliased lineage for {lineage}')

                    else:
                        pass

            else:
                error_list.append('Empty line')

            key = (line_number, display)

            if error_list:
                errors[key] = error_list



class LineageNotesException(Exception):
    def __init__(self, errors):
        self.errors: Dict = errors
        self.message = self.create_message(self.errors)
        super().__init__(self.message)

    @classmethod
    def create_message(cls, errors):
        message = dedent('''
            
            Lineage Notes Errors
            ---------------------            
            <<data>>
            ''')

        insert = ''

        for (line_number, line), error_list in errors.items():
            insert += f'- Line {line_number}:\t"{line}"\n'
            for index, error in enumerate(error_list):
                insert += f'  ({index + 1})\t{error}\n'
            insert += '\n'

        message = message.replace('<<data>>', insert or "None")

        return message


if __name__ == "__main__":

    print('Lineage Notes Analysis: Starting')

    check_data_integrity(file_name)

    if len(errors.keys()) != 0:
        raise LineageNotesException(errors)

    print('Lineage Note Analysis: No issues detected')
