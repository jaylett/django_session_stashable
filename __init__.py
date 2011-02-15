# Copyright (c) 2009 James Aylett <http://tartarus.org/james/computers/django/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

class SessionStashable(object):
    "Mixin this class to provide useful instance and class methods for stashing unsaved whatevers in the session."
    session_variable = 'object_stash' # if using this more than once, set explicitly on each class
    creator_field = 'created_by' # if you don't like this name, set explicitly on your derived class

    # Setting this to a string will add a context variable with that name
    # containing a count of unstashed models of this type.
    context_count_name = None

    def stash_in_session(self, session):
        "Stash this object in the current session."
        if getattr(self, self.creator_field)!=None:
            return # nothing to do
        if not session.has_key(self.session_variable):
            session[self.session_variable] = []
        if self.pk not in session[self.session_variable]:
            session[self.session_variable].append(self.pk)
            session.modified = True
        #print "stashed %s in session" % self
        
    def stashed_in_session(self, session):
        "Is this object stashed in the current session?"
        if getattr(self, self.creator_field)!=None:
            return False # non-anonymous should never be stashed
        if session.has_key(self.session_variable):
            stashed = session.get(self.session_variable)
            return self.pk in stashed
        return False
    
    @classmethod
    def clear_stashed_objects(cls, session):
        "Clear the sessions store for this object."
        #print "Clearing session store for %s" % cls
        if session.has_key(cls.session_variable):
            del session[cls.session_variable]
    
    @classmethod
    def reparent_all_my_session_objects(cls, session, user):
        "Go over the objects stashed in session and set user as their creator_field. Then clear the sessions store."
        cls.get_stashed_in_session(session).update(**{cls.creator_field: user})
        cls.clear_stashed_objects(session)

    @classmethod
    def num_stashed_in_session(cls, session):
        "Tell me how many objects are stashed in my session."
        try:
            r = len(session.get(cls.session_variable, []))
            #print "Found %i in %s" % (r, cls,)
            return r
        except:
            return 0

    @classmethod
    def get_stashed_in_session(cls, session):
        "Get all the objects stashed in my session."
        #print "Getting all %s stashed in session" % cls
        if session.has_key(cls.session_variable):
            return cls.objects.filter(id__in=session[cls.session_variable])
        else:
            return cls.objects.none()

    @classmethod
    def get_objects_for_request(cls, request):
        "Get all the objects either stashed in my session or owned by the user."
        if request.user.is_authenticated():
            return cls.objects.filter(
                ** {
                    cls.creator_field: request.user,
                }
            )
        else:
            return cls.get_stashed_in_session(request.session)

from django.db.models.loading import cache

def stashed_object_counts(request):
    """A context processor which adds counts of stashed objects
    of models which inherit from SessionStashable to RequestContext.

    To make a make a count appear for a particular model, set the
    class attribute context_count_name to an appropriate string
    to name its context variable, and enable this context processor
    in settings.py.
    """
    extra_context = {}
    for app in cache.get_apps():
        for model in cache.get_models(app):
            if issubclass(model, SessionStashable) and model.context_count_name:
                extra_context[model.context_count_name] = model.num_stashed_in_session(request.session)

    return extra_context
