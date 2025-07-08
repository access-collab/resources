# Visual Comparison of the Draft Delegated Act on Data Access (DDA) vs. the Adopted Delegated Act (DA)

**👉 [Click here to view the comparison](https://dsa40collaboratory.eu/dda-da-comparison)**

## Credits and Citation

The overview is based on work done by **LK Seiling** at the [DSA40 Data Access Collaboratory](https://dsa40collaboratory.eu/), who is responsible for splitting and aligning the texts to achieve a meaningful comparison. 

**Citation:**  
If you wish to cite this comparison, please use the following format:

> **LK Seiling** (2025). Comparison of the Draft and Adopted Delegated Act on Data Access. *DSA 40 Data Access Collaboratory*. Available at: [https://dsa40collaboratory.eu/dda-da-comparison/](https://dsa40collaboratory.eu/dda-da-comparison/)

---

## Run Locally

To generate the HTML file locally:

1. **Install Subversion**
   If you don't have Subversion (`svn`) installed, download it from [https://subversion.apache.org/packages.html](https://subversion.apache.org/packages.html).

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
