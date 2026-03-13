import pdfplumber


def extract_tables(pdf_path):

    tables_data = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                rows = []

                for row in table:

                    if row and len(row) >= 2:
                        rows.append({
                            "key": row[0],
                            "value": row[1]
                        })

                if rows:
                    tables_data.append(rows)

    return tables_data