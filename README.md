# scrape-itch-bundle
A selenium scraper written in python that scrapes the contents of an itch.io bundle.

When you buy a huge itch bundle, it all ends up on a frustrating, unsearchable, paginated site. The bundle items are seemingly placed at random across perhaps dozens of pages. This project scrapes the metadata about the items on those pages and makes them availabe in a human-readable yaml file. You can search and immediately know where the items that you want in your collection are. 


The example yaml file is for the Bundle for Racial Justice and Equality, which you should buy! 

https://itch.io/b/520/bundle-for-racial-justice-and-equality

To run this project:
1. set up python (3)
2. install the requirements file
3. place your personal information in a constants.yml file (see the provided example_constants)
4. put a chrome webdriver in a folder within your path (probably /usr/local/bin/)
5. and run the project!
