import json
import re
import sys, getopt

# Ment
MENT = 'ment'

with open('specification.json') as s:
    specification = json.load(s)

specific_words         = specification['specific_words']
specific_terms         = specification['specific_terms']
suffixes               = specification['suffixes']
word_segment_replacers = specification['word_segment_replacers']
safe_words             = specification['safe_words']

# Make suffixes only work at the end of words using regex
for i in range(len(suffixes)): suffixes[i] += r'\b'

# Word mentment
def suffixify(word):
    for suffix in suffixes:
        if re.search(suffix, word):
            return re.sub(suffix, MENT, word), True
    return word, False

# Word mentment
def mentment(word):
    # If a safe word, don't change it at all
    if word in safe_words:
        return word
    # If we have a hardcoded word, set it to that
    if word in specific_words:
        return specific_words[word]
    # Find a word segment replacer and use only the first one found if there is one
    for word_segment_replacer in word_segment_replacers:
        if word_segment_replacer in word:
            return word.replace(word_segment_replacer, word_segment_replacers[word_segment_replacer])
    # Add a suffix, if possible
    word, suffixified = suffixify(word)
    if suffixified:
        return word
    # Handle plurals (don't include things that end with "ss" like Grass)
    # This is recursive
    if word[-1] == 's' and word[-2] != 's':
        return mentment(word[0:-1])  + 's'
    return word + MENT

# Word replacement, whole words only
def replace_term(old, new, string):
    old = r'\b' + old + r'\b'
    return re.sub(old, new, string)

# Add a word to the word counter
def add_word(word, counter):
    if word in counter: counter[word] += 1
    else:               counter[word] =  1

def main():
    data = {}

    # Open JSON file
    print('Opening original file...')
    #with open('original.json', 'r', encoding='utf-8') as f:
    with open('original_GB.lang', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].split('#')[0]
        for line in lines:
            if not '=' in line: continue
            data[line.split('=')[0]] = line.split('=')[1]

    names = set()
    words = {}
    replacement_terms = {}

    # Find unique names
    print('Finding mobs and items...')
    for id in data:
        if id.startswith('tile.')        or\
        id.startswith('item.')        or\
        id.startswith('enchantment.') or\
        id.startswith('entity.'):
                if id == 'item.spawn_egg.entity.npc.failed': continue
                if id.startswith('enchantment.level'):       continue
                names.add(data[id])

    # Count words
    print('Finding words...')
    for name in names:
        for term in name.split():
            add_word(term, words)

    # Change words
    print('The mentment has begun...')
    for term in words:
        # Don't mentify words that aren't capitalised. Items are in title case, so this will mostly be prepositions.
        if term != term.capitalize() and term != term.upper(): continue
        # The word substitution stuff is probably too compliacted to mess with
        if '%' in term: continue
        replacement_terms[term] = mentment(term)

    # Add the multi word terms to replacement_terms
    for term in specific_terms:
        replacement_terms[term] = specific_terms[term]
        # Handle the case of them being at the start of a sentence, eg. "Brewing stand" vs "Brewing Stand" or "brewing stand"
        replacement_terms[term.capitalize()] = specific_terms[term].capitalize()

    # Add words that haven't already been added (ie. hardcoded words that aren't in an item name)
    for specific_word in specific_words:
        if specific_word not in replacement_terms:
            replacement_terms[specific_word] = specific_words[specific_word]

    # Add word lower case versions and plurals
    print('Adding plurals and lower case words...')
    for replacement_word in replacement_terms.copy():
        replacement_terms[replacement_word.lower()] = replacement_terms[replacement_word].lower()

    for replacement_word in replacement_terms.copy():
        if replacement_word[-1] == 's': 
            replacement_terms[replacement_word + 'es'] = replacement_terms[replacement_word] + 'es'
            continue
        replacement_terms[replacement_word + 's'] = replacement_terms[replacement_word] + 's'

    # Substitution of mented names into long names
    print('Finalising names...')
    for id in data:
        # Do specific terms first - "Blastment Table" not "Blastment Smeltment Table"
        for term in specific_terms:
            if term in data[id]:
                data[id] = replace_term(term, replacement_terms[term], data[id])
        for term in replacement_terms:
            if term in data[id]:
                data[id] = replace_term(term, replacement_terms[term], data[id])

    # Write to file
    print('Saving...')
    with open('en_US.lang', 'w', encoding='utf-8') as f:
        for datum in data:
            f.write(f'{datum}={data[datum]}\n')

    print('Done.')

if __name__ == '__main__':
    main()
