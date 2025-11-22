# Kaggle Setup Guide

Quick guide to get the ADE Healthcare Documentation system running on Kaggle.

## Step 1: Get Your Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key (you'll need it in Step 3)

## Step 2: Create a New Kaggle Notebook

1. Go to [Kaggle](https://www.kaggle.com)
2. Click on "Code" in the top navigation
3. Click "New Notebook"
4. Upload the `ade_healthcare_documentation.ipynb` file
   - Click "File" → "Upload Notebook"
   - Select the notebook file

## Step 3: Add Your API Key as a Secret

1. In your Kaggle notebook, click "Add-ons" in the right sidebar
2. Scroll down to "Secrets"
3. Click "+ Add a new secret"
4. Label: `GOOGLE_API_KEY`
5. Value: Paste your Gemini API key from Step 1
6. Click "Add"

## Step 4: Enable Internet Access

1. In the right sidebar, under "Settings"
2. Toggle "Internet" to ON
3. This is required for the Gemini API calls

## Step 5: Run the Notebook

1. Click "Run All" or execute cells one by one
2. The first cell will install dependencies (takes ~1 minute)
3. Subsequent cells initialize the system and run the demo

## Step 6: Customize for Your Data

Replace the sample data dictionary with your own:

```python
# Instead of the sample_data_dictionary, use your own
your_data_dictionary = """
Variable Name,Field Type,Field Label,Choices,Notes
your_var_1,text,Your Variable 1,,Description
your_var_2,integer,Your Variable 2,,Description
...
"""

job_id = orchestrator.process_data_dictionary(
    source_data=your_data_dictionary,
    source_file="your_study.csv",
    auto_approve=False  # Set to True to skip manual review
)
```

## Step 7: Review and Approve

If `auto_approve=False`:

```python
# Get pending items
pending = orchestrator.review_queue.get_pending_items(job_id)

# Review first item
print(pending[0].generated_content)

# Approve
orchestrator.review_queue.approve_item(pending[0].item_id)

# Or approve with edits
edited_content = pending[0].generated_content + "\n\n**Reviewed by: Your Name**"
orchestrator.review_queue.approve_item(pending[0].item_id, edited_content)
```

## Step 8: Generate Final Documentation

```python
# Create final documentation
documentation = orchestrator.finalize_documentation(
    job_id=job_id,
    output_file="my_documentation.md"
)

# Download the file
from IPython.display import FileLink
FileLink("my_documentation.md")
```

## Troubleshooting

### "Secret not found" error
- Make sure the secret is named exactly `GOOGLE_API_KEY`
- Check that you saved the secret
- Try restarting the kernel

### "API key not valid" error
- Verify your API key in Google AI Studio
- Make sure Gemini API is enabled for your account
- Check for extra spaces when copying the key

### "Module not found" error
- Run the first cell again to install dependencies
- Make sure you're using a Python notebook (not R)

### Notebook is slow
- Gemini API calls take a few seconds each
- For large data dictionaries, consider processing in batches
- Use `auto_approve=True` for faster processing

### Database locked error
- Click "Restart Kernel" in Kaggle
- Re-run the initialization cells

## Tips for Best Results

1. **Start Small**: Test with 3-5 variables first
2. **Use Toons**: Create instruction Toons for consistent mapping
3. **Review Carefully**: Check the first few variables before auto-approving
4. **Save Often**: Download your database file periodically
5. **Iterate**: Refine system prompts based on your domain

## Example Data Formats

The system accepts various formats. Here are examples:

### REDCap Format
```csv
Variable Name,Field Type,Field Label,Choices,Notes
patient_id,text,Patient ID,,Unique
age,integer,Age,,"Years"
```

### Simple CSV
```csv
variable,type,description
patient_id,string,Unique patient identifier
age,integer,Patient age in years
```

### JSON Format
```json
[
  {
    "variable": "patient_id",
    "type": "string",
    "description": "Unique patient identifier"
  }
]
```

## Next Steps

After your first successful run:

1. **Customize Agents**: Modify system prompts for your domain
2. **Create Toons**: Build a library of reusable instructions
3. **Batch Processing**: Process multiple data dictionaries
4. **Export Results**: Download and share documentation

## Need Help?

- Check the main README.md for detailed documentation
- Review cell comments in the notebook
- Open an issue on GitHub

## Kaggle-Specific Features

### Save Your Work
```python
# Backup database to Kaggle output
import shutil
shutil.copy2("project.db", "/kaggle/working/project_backup.db")
```

### Download Files
```python
from IPython.display import FileLink

# Download database
FileLink("project.db")

# Download documentation
FileLink("healthcare_data_documentation.md")
```

### Use Kaggle Datasets
```python
# If you've uploaded a dataset to Kaggle
import pandas as pd

df = pd.read_csv("/kaggle/input/your-dataset/data_dictionary.csv")
data_dict = df.to_csv(index=False)

job_id = orchestrator.process_data_dictionary(
    source_data=data_dict,
    source_file="kaggle_dataset.csv"
)
```

---

Happy documenting!
