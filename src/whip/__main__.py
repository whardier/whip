import uvicorn


def main():
    """Start the WHIP server"""
    uvicorn.run(
        "whip.main:app",
        host="0.0.0.0",
        port=9447,
        reload=False,
    )


if __name__ == "__main__":
    main()
