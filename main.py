import logging
import os
import time
import schedule
from FireflyIII import FireflyIII
from HistoryManager import HistoryManager
from SW import SW

logging.basicConfig(
    filename=os.path.join("data", "sync2ff.log"),
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s'
)


def getDefaultTags() -> list:
    """Retrieve default tags for transaction export to FireflyIII"""
    default_tags_str = os.getenv("DEFAULT_TAGS", "Splitwise")
    default_tags = default_tags_str.strip().split()
    return default_tags


def run_export(ff: FireflyIII, sw: SW, hm: HistoryManager) -> None:
    # Export transactions
    hm.loadHistory()
    print(
        f"Exporting transactions to Firefly [FIRST EXPORT: {str(hm.isFirstExport())} - START_DATE: {hm.getLastSplitwiseExport()}]")
    sw.exportToFirefly(ff, default_src=os.getenv("FF_DEFAULT_SRC", "Unclassified_SRC"),
                       default_dest=os.getenv("FF_DEFAULT_DST", "Unclassified"),
                       exportStartDate=hm.getLastSplitwiseExport(), tag=getDefaultTags(),
                       firstExport=hm.isFirstExport())
    # Export liabilities
    # TODO Missing import liabilities implementation
    sw.manageLiabilitiesToFirefly(ff)
    # Store export
    hm.storeHistory()
    print("Export successful")
    logging.info("Export successful")


def main():
    logging.info("Sync2FF - Started")

    hm = HistoryManager()
    try:
        ff = FireflyIII(os.getenv("FF_URL"), os.getenv("FF_TOKEN"))
        sw = SW(os.getenv("SW_CONSUMER_KEY"), os.getenv("SW_CONSUMER_SECRET"), os.getenv("SW_API_KEY"), logging.getLogger())
        logging.info("Setup completed")
    except ValueError as e:
        print(f"Please provide required parameters: {e}")
        logging.warning(f"Missing required parameters: {e}")
        exit(1)

    # Evaluate massive deletion of last EXPORT
    deletePreviousImport = os.getenv("DELETE_PREVIOUS_EXPORT", "False").lower() in ('true', '1', 't')
    if deletePreviousImport:
        print("Deleting previous import...")
        ff.deleteTransactionsThisTag(getDefaultTags())
        print("Deletion completed")
        logging.info("Deletion completed")

    schedule.every().day.do(run_export, ff=ff, sw=sw, hm=hm)
    print("Scheduled daily export")
    logging.info("Scheduled daily export")

    schedule.run_all()

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
