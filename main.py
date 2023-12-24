import os
from FireflyIII import FireflyIII
from SW import SW


def getDefaultTags() -> list:
    """Retrieve default tags for transaction export to FireflyIII"""
    default_tags_str = os.getenv("DEFAULT_TAGS", "Splitwise")
    default_tags = default_tags_str.strip().split()
    return default_tags


def getLastSplitwiseExport() -> str:
    if isFirstExport():
        return "2011-01-01"
    else:
        # TODO Create a mechanism to evaluate last Firefly export
        return "2011-01-01"


def isFirstExport() -> bool:
    # TODO Create a mechanism to evaluate if it is the first import
    return True


def main():
    try:
        ff = FireflyIII(os.getenv("FF_URL"), os.getenv("FF_TOKEN"))
        sw = SW(os.getenv("SW_CONSUMER_KEY"), os.getenv("SW_CONSUMER_SECRET"), os.getenv("SW_API_KEY"))
    except ValueError as e:
        print(f"Please provide required parameters: {e}")
        exit(1)

    # Evaluate massive deletion of last EXPORT
    deletePreviousImport = os.getenv("DELETE_PREVIOUS_EXPORT", "False").lower() in ('true', '1', 't')
    if deletePreviousImport:
        print("Deleting previous import...")
        ff.deleteTransactionsThisTag(getDefaultTags())
        print("Deletion completed")

    # Export transactions
    print(f"Exporting transactions to Firefly [FIRST EXPORT: {str(isFirstExport())} - START_DATE: {getLastSplitwiseExport()}]")
    sw.exportToFirefly(ff, exportStartDate=getLastSplitwiseExport(), default_src=os.getenv("FF_DEFAULT_SRC", "Unclassified_SRC"),
                       default_dest=os.getenv("FF_DEFAULT_DST", "Unclassified"), tag=getDefaultTags(), firstExport=isFirstExport())
    # Export liabilities
    # TODO Missing import implementation
    sw.manageLiabilitiesToFirefly(ff)


if __name__ == "__main__":
    main()
