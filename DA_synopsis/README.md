# Visual Comparison of the Draft Delegated Act on Data Access (DDA) vs. the Adopted Delegated Act (DA)

**👉 [Click here to view the comparison](https://dsa40collaboratory.eu/wp-content/uploads/2025/07/compare_DDA_DA.html){:target="_blank"}**

---

## Run Locally

To generate the HTML file locally:

1. **Install Subversion**
   If you don't have Subversion (`svn`) installed, download it from [https://subversion.apache.org/packages.html](https://subversion.apache.org/packages.html){:target="_blank"}.

2. **Download the script and data**
   Run the following command in your terminal:

   ```bash
   svn export https://github.com/access-collab/resources/trunk/DA_synopsis
   ```
   
3. **Install Python dependencies**
    Ensure you have Python 3 installed, then install the required packages:
    
    ```bash
   pip install -r requirements.txt
   ```
   
4. **Generate the HTML**
    Run the script to create the comparison page:
     
    ```bash
   python3 make_html.py
   ```
