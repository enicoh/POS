
import os

target_file = 'pos_routes.py'

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start and end of the function generate_sales_report_pdf_download
start_line_idx = -1
end_line_idx = -1

for i, line in enumerate(lines):
    if 'def generate_sales_report_pdf_download():' in line:
        start_line_idx = i
        break

if start_line_idx == -1:
    print("Function not found!")
    exit(1)

# Find the end (start of next function or end of file)
# The next function starts with @ or def at root level?
# Actually, we know it ends before @pos_api.route('/upload/image'
for i in range(start_line_idx + 1, len(lines)):
    if lines[i].startswith('@pos_api.route(\'/upload/image\''):
        end_line_idx = i
        break

if end_line_idx == -1:
    print("End of function not found")
    # Maybe it's the last function? No, we saw more code.
    exit(1)

# Inspect the lines to wrap
func_body = lines[start_line_idx:end_line_idx]

# We want to keep the def line and docstring
# Def is lines[start_line_idx]
# Docstring is lines[start_line_idx+1] to ...

# Let's verify standard structure
# def generate_sales_report_pdf_download():
#     """..."""
#     token = ...

# We want to keep the def line and docstring, and the auth logic.
# Wait, the auth logic does returns usage of token.
# My proposed try/except block started AFTER the auth logic in my previous attempts?
# No, my replacement replaced from `token = request.args.get('token')` ?
# NO. In my last attempt (Step 280 replacement content), I started at `# Reuse the alias logic for generating PDF` which is line 1175.
# The endpoint starts at line 1145!

# Ah, I was only wrapping the LATTER PART of the function.
# The auth part is fine (it returns JSON).
# The crash is likely in the query/PDF generation part.
# So I should only wrap from `# Reuse the alias logic...` (line 1175 approx)
# to the end of the function.

# Let's find line with `# Reuse the alias logic for generating PDF`
logic_start_idx = -1
for i in range(start_line_idx, end_line_idx):
    if '# Reuse the alias logic for generating PDF' in lines[i]:
        logic_start_idx = i
        break

if logic_start_idx == -1:
    print("Logic start comment not found")
    exit(1)

# Content to indent
content_to_indent = lines[logic_start_idx:end_line_idx]

# New content construction
new_content = []
# 1. Keep everything before logic_start_idx
new_content.extend(lines[:logic_start_idx])

# 2. Add try:
new_content.append('    # Reuse the alias logic for generating PDF\n')
new_content.append('    try:\n')

# 3. Add indented content (excluding the comment line we already added)
# The comment line was lines[logic_start_idx].
for line in lines[logic_start_idx+1:end_line_idx]:
    # Check if empty line (just newline)
    if line.strip() == '':
        new_content.append(line)
    else:
        new_content.append('    ' + line)

# 4. Add except block
new_content.append('\n')
new_content.append('    except Exception as e:\n')
new_content.append('        logger.error(f"Error generating PDF report: {str(e)}")\n')
new_content.append('        import traceback\n')
new_content.append('        logger.error(traceback.format_exc())\n')
new_content.append('        return jsonify({\'error\': f\'Server error: {str(e)}\'}), 500\n')
new_content.append('\n')

# 5. Add everything after end_line_idx
new_content.extend(lines[end_line_idx:])

# Write back
with open(target_file, 'w', encoding='utf-8') as f:
    f.writelines(new_content)

print("Successfully applied try/except block.")
