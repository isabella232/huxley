# Huxley

*Watches you browse, takes screenshots, tells you when they change*

Huxley is a test-like system for catching **visual regressions** in Web applications. It was originally built by [Pete Hunt](http://github.com/petehunt/) with input from [Maykel Loomans](http://www.miekd.com/) at [Instagram](http://www.instagram.com/).

## Installation instructions

* Get [Selenium Server](http://docs.seleniumhq.org/download/)
* Install Firefox and add the binary to your PATH
	* `export PATH=/Applications/Firefox.app/Contents/MacOS:$PATH` (or create a symbolic link that within the searchable path)
* (optional) Install Chromedriver
	* `brew install chromedriver`

Install to command line with `python setup.py install`

## Getting started

### 1. Fire up your app

On Lyft, use vagrant. Otherwise, start up a python simpleserver `python -m SimpleHTTPServer 11080`.

### 2. Create a Huxleyfile

A Huxleyfile describes your test. Create one that looks like this:

```
[homepage]
url=http://localhost:11080/
```

This creates a test named `homepage` that tests the URL `http://localhost:11080/`.

### 3. Start your local Selenium Server (skip if using remote server)

`java -jar selenium-server-standalone-XXX.jar`

### 4. Record the test

`huxley --record`

Huxley records `click`, `keyup`, and `scroll` events along with the delay between events.  There is currently no support for tracking navigation outside the angular app. Hit "enter" in the huxley terminal window when you want to take a screenshot. When you're done recording, type "q" then "enter" in the huxley terminal.

After confirming, Huxley will automatically record the test for you and save it to disk as `homepage.huxley`. Be sure to commit the `Huxleyfile` as well as `homepage.huxley` into your repository so you can track changes to them.

### 5. Test UI changes & Playback

Simply run the `huxley` command in the same directory as the `Huxleyfile` to be sure that your app still works. By default huxley will re-record and overwrite any changes to the screenshots so you can review and check in the new screenshot files to the repo as needed. 


## Huxleyfile options

| Option | Example | Description |
| ------ | ------- | ----------- |
| url | `url=http://localhost:11080/` | Url to visit |
| sleepfactor | `sleepfactor=0.5` | Multiplier to speed up / slow down execution time |
| screensize | `screensize=320x568` | For testing responsive design, change viewport size |
| filename | `filename=foo` | To save the directory name as something other than the TESTNAME.huxley |
| postdata | `postdata=data.json` | File for POST data |

## What about CI?

If you're using a continuous integration solution like [Jenkins](http://jenkins-ci.org/) you probably don't want to automatically rerecord screen shots on failure. Simply run `huxley --playback-only` to do this.

## Best practices

Integration tests sometimes get a bad rap for testing too much at once. We've found that if you use integration tests correctly they can be just as effective and accurate as unit tests. Simply follow a few best practices:

* **Don't test a live app. Use mocking to make your components reliable instead.** If you hit your live app, failures in any number of places could trigger false failures in your UI tests. Instead of hitting a real URL in your app, **create a dedicated test URL** for Huxley to hit that uses mocking (and perhaps dependency injection) to isolate your UI component as much as possible. Huxley is completely unopinionated; use whatever tools you want to do this.
* **Test a small unit of functionality.** You should try to isolate your UI into modular components and test each one individually. Additionally, try to test one interaction per Huxley test so that when it fails, it's easy to tell exactly which interaction is problematic and it's faster to re-run it.

## Technical FAQ

### Why does Huxley stop recording when I navigate away from the page?

Huxley is designed for testing JavaScript UI components at this time. We've found that you can test multiple pages by creating a new Huxley test for each URL. This is valuable even if you don't use the interactive features of Huxley because it will ensure your static pages stay pixel perfect.

### I can't tell what changed!

It's usually best if you use an image comparison tool like [Kaleidoscope](http://www.kaleidoscopeapp.com/) to tell what changed. But Huxley includes a simple image diff tool; simply run `huxley` with the `--save-diff` option to output a `diff.png` which will show you the pixels that changed.

### How do I use a remote webdriver server?

You can set the `HUXLEY_WEBDRIVER_LOCAL` environment variable to tell Huxley which webdriver URL to use for `--record` mode. You can set the `HUXLEY_WEBDRIVER_REMOTE` environment variable to tell Huxley which webdriver URL to use for screenshots and playback. Usually you only need to use this when working in a team setting such that everyone's screenshots are taken on the same machine configuration (otherwise they'll change depending on who ran them last).

