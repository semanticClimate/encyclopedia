# Transcript Processing Tools

This directory contains tools for converting raw transcripts into clean, well-formatted markdown documents.

## Features

- **Remove timestamps and dates** - Automatically detects and removes various time/date formats
- **Join sentences** - Properly combines sentences that were split across lines
- **Remove filler words** - Eliminates "um", "er", "uh", "like", "you know", etc.
- **Remove repeated words** - Cleans up consecutive repeated words
- **Format as markdown** - Creates properly structured markdown with sections and paragraphs
- **Auto-detect sections** - Identifies section headers and organizes content accordingly

## Files

- `transcript_processor.py` - Main processing script
- `process_all_transcripts.py` - Batch processing for multiple files
- `sample_transcript.txt` - Example input file
- `sample_output_improved.md` - Example output file

## Usage

### Single File Processing

```bash
python transcript_processor.py input_file.txt output_file.md
```

Example:
```bash
python transcript_processor.py my_transcript.txt my_transcript_cleaned.md
```

### Batch Processing

```bash
python process_all_transcripts.py
```

This will automatically find and process all transcript files in the current directory.

## Input Format

The processor can handle various transcript formats:

### With Timestamps
```
[00:00:15] Welcome to our discussion about climate change research.
[00:00:30] Introduction
So, um, today we're going to talk about climate change.
```

### With Section Headers
```
Introduction
Today we're going to discuss climate change research.

Main Topics
We need to focus on three main areas.
```

### Mixed Format
```
[00:01:15] Main Topics
Well, basically, we need to focus on three main areas.
```

## Output Format

The processor creates clean markdown with:

- **Section headers** (## Header Name)
- **Proper paragraphs** with joined sentences
- **Clean text** without filler words or timestamps
- **Consistent formatting** throughout

Example output:
```markdown
## Introduction

Welcome to our discussion about climate change research. Today we're going to talk about climate change and how we can improve our understanding of global warming.

## Main Topics

We need to focus on three main areas. First, we have temperature data. Second, we have precipitation patterns. And third, we have sea level rise.
```

## Customization

### Adding Filler Words

To add more filler words to remove, edit the `filler_words` set in `transcript_processor.py`:

```python
self.filler_words = {
    'um', 'er', 'uh', 'ah', 'like', 'you know', 'so', 'well', 'actually',
    'basically', 'literally', 'obviously', 'clearly', 'right', 'okay',
    'ok', 'yeah', 'yes', 'no', 'mm', 'hmm', 'huh',
    'your_custom_word'  # Add your own filler words here
}
```

### Modifying Time Patterns

To handle different timestamp formats, edit the `time_patterns` list:

```python
self.time_patterns = [
    r'\d{1,2}:\d{2}(?::\d{2})?',  # HH:MM or HH:MM:SS
    r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',  # 12-hour format
    r'\[\d{1,2}:\d{2}(?::\d{2})?\]',  # [HH:MM:SS]
    r'\(\d{1,2}:\d{2}(?::\d{2})?\)',  # (HH:MM:SS)
    r'your_custom_pattern'  # Add your own patterns here
]
```

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Examples

### Example 1: Basic Processing

Input (`transcript.txt`):
```
[00:00:15] Welcome to our discussion.
[00:00:30] Introduction
So, um, today we're going to talk about, er, climate change research.
```

Command:
```bash
python transcript_processor.py transcript.txt transcript_clean.md
```

Output (`transcript_clean.md`):
```markdown
## Introduction

Welcome to our discussion. Today we're going to talk about climate change research.
```

### Example 2: Batch Processing

If you have multiple transcript files:
- `meeting1_transcript.txt`
- `meeting2_transcript.txt` 
- `interview_transcript.md`

Run:
```bash
python process_all_transcripts.py
```

This will create:
- `meeting1_transcript_cleaned.md`
- `meeting2_transcript_cleaned.md`
- `interview_transcript_cleaned.md`

## Troubleshooting

### Common Issues

1. **No sections detected**: The processor might not recognize section headers. Try adding clear section markers like "## Section Name" or "Section Name:" in your transcript.

2. **Filler words not removed**: Add specific filler words to the `filler_words` set in the processor.

3. **Timestamps not removed**: Add new timestamp patterns to the `time_patterns` list.

4. **Encoding issues**: Make sure your input files are UTF-8 encoded.

### Getting Help

If you encounter issues:

1. Check that your input file is properly formatted
2. Verify the file encoding (should be UTF-8)
3. Try processing a small sample first
4. Check the console output for error messages

## License

This tool is part of the encyclopedia project and follows the same licensing terms.





