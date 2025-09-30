# Reddit Data Structure Documentation

## Overview
This document describes the data structure used to store Reddit posts and comments in the Workbench DIY project.

## Data Flow
```
submission (Reddit API object) → reddit_post (dictionary) → all_data (list of dictionaries)
```

## reddit_post Dictionary Structure

### Top-Level Structure
The `reddit_post` dictionary contains 6 key-value pairs:

```python
reddit_post = {
    'post_id': '1n695i4',                    # String: Reddit post ID
    'title': 'I messed up, and I hate myself', # String: Post title
    'content': 'Shoud\u2019ve turned the support studs...', # String: Post body text
    'score': 6661,                           # Integer: Upvotes/downvotes
    'permalink': 'https://reddit.com/r/DIY/comments/1n695i4/i_messed_up_and_i_hate_myself/', # String: Full URL
    'comments': [...]                        # List: List of comment dictionaries
}
```

### List Structure: 'comments'
The `comments` key contains a list of dictionaries (0-5 comments per post):

```python
'comments': [
    {
        'post_id': '1n695i4',            # String: Links back to parent post
        'comment_id': 'nbyf9dz',         # String: Reddit comment ID
        'body': 'Are you storing loose ball bearings on the shelves? No? Then it\u2019s good enough.', # String: Comment text
        'score': 13365                   # Integer: Comment upvotes/downvotes
    },
    {
        'post_id': '1n695i4',
        'comment_id': 'nbyffta', 
        'body': 'Is shelf.',
        'score': 803
    }
    # ... up to 5 comments total
]
```
## List Structure: 'all_data'

The `all_data` variable is a list that stores multiple `reddit_post` dictionaries, each representing a single Reddit post and its associated comments.

### Structure Example
```python
all_data = [
    {
        'post_id': '1n695i4',
        'title': 'I messed up, and I hate myself',
        'content': 'Shoud\u2019ve turned the support studs...',
        'score': 6661,
        'permalink': 'https://reddit.com/r/DIY/comments/1n695i4/i_messed_up_and_i_hate_myself/',
        'comments': [
            {
                'post_id': '1n695i4',
                'comment_id': 'nbyf9dz',
                'body': 'Are you storing loose ball bearings on the shelves? No? Then it\u2019s good enough.',
                'score': 13365
            },
            {
                'post_id': '1n695i4',
                'comment_id': 'nbyffta',
                'body': 'Is shelf.',
                'score': 803
            }
        ]
    },
    {
        'post_id': '1n6a2b3',
        'title': 'DIY Bookshelf Completed!',
        'content': 'Built my first bookshelf from scratch. Used pine and oak for the frame.',
        'score': 2450,
        'permalink': 'https://reddit.com/r/DIY/comments/1n6a2b3/diy_bookshelf_completed/',
        'comments': [
            {
                'post_id': '1n6a2b3',
                'comment_id': 'nbz1abc',
                'body': 'Looks great! How long did it take you?',
                'score': 210
            },
            {
                'post_id': '1n6a2b3',
                'comment_id': 'nbz1xyz',
                'body': 'What finish did you use?',
                'score': 98
            }
        ]
    }
]
```


## Key Points

### Data Types
- **Strings**: post_id, title, content, permalink, comment_id, body
- **Integers**: score (both post and comment scores)
- **Lists**: comments list
- **Dictionaries**: reddit_post itself, each comment in comments list

### Nested Structure
- **reddit_post** = Dictionary with 6 key:value pairs
- **5 values** = Simple data (strings, integers)
- **1 value** (`comments`) = List of dictionaries


### Unicode Handling
- Text may contain Unicode escape sequences like `\u2019` (smart quotes)
- Text cleaning normalizes these to standard ASCII characters

## Usage Examples

### Accessing Data
```python
# Access post information
post_title = reddit_post['title']
post_score = reddit_post['score']

# Access comments
comments_list = reddit_post['comments']
first_comment = reddit_post['comments'][0]
first_comment_body = reddit_post['comments'][0]['body']
```

### Iterating Through Comments
```python
for comment in reddit_post['comments']:
    comment_id = comment['comment_id']
    comment_body = comment['body']
    comment_score = comment['score']
```

### Modifying Data
```python
# Add cleaned text field
reddit_post['clean_text'] = cleaned_content

# Add comment to list
new_comment = {
    'post_id': reddit_post['post_id'],
    'comment_id': 'new_id',
    'body': 'New comment text',
    'score': 0
}
reddit_post['comments'].append(new_comment)
```

## Storage
- **all_data**: List containing all `reddit_post` dictionaries
- **JSON format**: Stored as `reddit-test-data.json`
- **Processing**: Each `reddit_post` in `all_data` gets processed for text cleaning

## Related Files
- `ingest-reddit.py`: Creates reddit_post dictionaries from Reddit API
- `file-name`: Contains serialized all_data list

---

## Reference: Array vs List

**In Python, there's no "array" - only lists!**

- **Array**: A term from other programming languages (C, Java, JavaScript)
- **List**: Python's data structure for ordered collections
- **In Python docs**: People often say "array" but mean "list"

**Python List = Array in Other Languages:**

```python
# Python List
my_list = ['apple', 'banana', 'cherry']
print(my_list[0])  # 'apple' - indexed access
print(my_list[1])  # 'banana' - ordered
```

```javascript
// JavaScript Array (same concept)
let myArray = ['apple', 'banana', 'cherry'];
console.log(myArray[0]);  // 'apple' - same indexed access
```

**Key Characteristics:**
- **Indexed**: Access items by position `[0]`, `[1]`, `[2]`
- **Ordered**: Items stay in the order you put them
- **Mutable**: You can add, remove, change items
- **Can hold any data type**: Strings, numbers, dictionaries, other lists

**What is `comments`?**
```python
reddit_post = {
    'comments': [                    # ← This is a LIST
        {                           # ← Dictionary #1 in the list
            'comment_id': 'abc123',
            'body': 'First comment'
        },
        {                           # ← Dictionary #2 in the list  
            'comment_id': 'def456',
            'body': 'Second comment'
        }
    ]
}
```

**`comments` is:**
- A **Python list** (not an array)
- A **list of dictionaries**
- Each item in the list is a **comment dictionary**
